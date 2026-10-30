"""任务分发 handler（AgentKit 的 agent_callable）。

每个任务按 ``task_type`` 分发到对应处理逻辑，输出 dict 作为任务结果回写 Redis。
- 解析/问答/生成/优化复用现有 ``services`` 层的纯业务函数与 ``agent`` 层的已编译图；
- 模拟面试为多轮交互，用 Redis 会话状态 + 服务函数手工驱动（等价于 LangGraph 的
  ask/evaluate 状态机，但更契合「每轮一个任务」的队列模型）；
- 所有同步/阻塞调用（LLM、Redis、PG）经 ``asyncio.to_thread`` 包装，避免阻塞 worker 事件循环。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid

import redis

from agent.graph import parse_engine
from agent.mock_interview import DEFAULT_RATIO, LEVEL_MAP, _flatten_questions
from config.setting import get_settings
from db import repositories
from services.edit_engine.skills import generate_resume, optimize_skills
from services.edit_engine.version import apply_suggestions, diff_versions, version_store
from services.qa_engine.answer import generate_answer
from services.qa_engine.evaluate import evaluate_answer
from services.qa_engine.intent import recognize_intent
from services.qa_engine.memory import desensitize, memory_store, new_session_id
from services.qa_engine.question_generate import generate_questions
from services.qa_engine.retrieval import flatten_fields
from services.qa_engine.summarize import summarize_report
from taskqueue.context import (
    build_coaching_context,
    build_edit_context,
    build_mock_interview_context,
    build_parse_context,
)
from taskqueue.storage import load_file

settings = get_settings()

_MOCK_PREFIX = "mock:session:"


async def _run(func, *args, **kwargs):
    """在线程池中执行同步/阻塞调用。"""
    return await asyncio.to_thread(func, *args, **kwargs)


def _mock_client() -> redis.Redis:
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
        socket_connect_timeout=2,
    )


async def resume_agent_handler(ctx) -> dict:
    """Redis 队列任务总入口，按 task_type 分发。"""
    context = ctx.context or {}
    task_type = context.get("task_type") or "unknown"
    user_id = context.get("user_id") or "anonymous"

    await _run(repositories.update_task_status, ctx.task_id, "processing")

    try:
        result = await _dispatch(ctx, task_type, context, user_id)
        await _run(repositories.update_task_status, ctx.task_id, "done")
        return result
    except Exception as e:  # noqa: BLE001 - 统一兜底，回传结构化错误
        await _run(repositories.update_task_status, ctx.task_id, "failed")
        return {"error": {"code": "INTERNAL", "module": task_type, "message": str(e)}}


async def _dispatch(ctx, task_type: str, context: dict, user_id: str) -> dict:
    if task_type == "parse":
        return await _handle_parse(ctx, context, user_id)
    if task_type == "coaching":
        return await _handle_coaching(ctx, context, user_id)
    if task_type == "mock_interview":
        return await _handle_mock_interview(ctx, context, user_id)
    if task_type == "edit.generate":
        return await _handle_edit_generate(ctx, context, user_id)
    if task_type == "edit.optimize":
        return await _handle_edit_optimize(ctx, context, user_id)
    if task_type == "edit.apply":
        return await _handle_edit_apply(ctx, context, user_id)
    if task_type == "edit.diff":
        return await _handle_edit_diff(ctx, context, user_id)
    return {"error": {"code": "UNKNOWN_TASK", "module": "dispatch", "message": f"未知任务类型 {task_type}"}}


# ---------------------------------------------------------------------------
# 简历解析
# ---------------------------------------------------------------------------

async def _handle_parse(ctx, context: dict, user_id: str) -> dict:
    file_id = context.get("file_id")
    file_name = context.get("file_name") or "resume"
    if not file_id:
        return {"error": {"code": "PARSE_EMPTY", "module": "parse", "message": "缺少文件，请重新上传"}}

    data = await _run(load_file, file_id)
    if not data:
        return {"error": {"code": "PARSE_EMPTY", "module": "parse", "message": "文件已过期，请重新上传"}}

    await ctx.emitter.emit("开始解析简历")
    state = await _run(parse_engine.invoke, {"file_source": data, "file_name": file_name})

    if state.get("error_data"):
        return {"error": state["error_data"]}

    fields = state.get("fields") or {}
    pending = state.get("pending") or []
    resume_id = f"rsm_{uuid.uuid4().hex[:8]}"
    file_hash = hashlib.sha256(data).hexdigest()
    source_type = state.get("source_type") or state.get("file_type") or ""
    ocr_used = bool(state.get("ocr_used"))

    # 落库：resumes（唯一数据源）+ resume_versions v1
    await _run(
        repositories.create_resume,
        resume_id, user_id, fields, pending,
        name=file_name, source_type=source_type, ocr_used=ocr_used, file_hash=file_hash,
    )
    await _run(version_store.save, resume_id, "v1", fields, "initial parse")

    await ctx.emitter.emit("解析完成")
    return {
        "resume_id": resume_id,
        "source": {"type": source_type, "ocr_used": ocr_used, "file_type": source_type},
        "fields": fields,
        "pending": pending,
        "file_valid": True,
    }


# ---------------------------------------------------------------------------
# 面试辅导（多轮问答，每轮一个任务）
# ---------------------------------------------------------------------------

async def _handle_coaching(ctx, context: dict, user_id: str) -> dict:
    payload = build_coaching_context(context)
    fields = payload["fields"]
    question = payload["question"]
    if not fields:
        return {"error": {"code": "QA_NO_RESUME", "module": "coaching", "message": "请先上传并解析简历"}}
    if not question:
        return {"error": {"code": "QA_NO_QUESTION", "module": "coaching", "message": "问题为空"}}

    await ctx.emitter.emit("识别问题意图")
    intent = await _run(recognize_intent, question)
    retrieved = await _run(flatten_fields, fields)
    if not retrieved:
        return {"error": {"code": "QA_RETRIEVE_EMPTY", "module": "coaching", "message": "未找到可用的简历信息"}}

    await ctx.emitter.emit("生成参考答案")
    answer = await _run(generate_answer, question, intent["intent"], retrieved)

    session_id = context.get("session_id") or new_session_id()
    turn = {"question": desensitize(question), "answer": desensitize(answer["answer"])}
    history = await _run(memory_store.append, session_id, turn)

    return {
        "session_id": session_id,
        "answer": answer["answer"],
        "citations": answer["citations"],
        "intent": intent["intent"],
        "history": history,
    }


# ---------------------------------------------------------------------------
# 模拟面试（多轮交互：start / answer）
# ---------------------------------------------------------------------------

async def _handle_mock_interview(ctx, context: dict, user_id: str) -> dict:
    payload = build_mock_interview_context(context)
    fields = payload["fields"]
    action = payload["action"]
    session_id = context.get("session_id") or new_session_id()

    if not fields:
        return {"error": {"code": "QA_NO_RESUME", "module": "mock_interview", "message": "请先上传并解析简历"}}
    if not fields.get("experience"):
        return {"error": {"code": "QA_NO_EXPERIENCE", "module": "mock_interview", "message": "简历信息不足，请补充关键经历"}}

    if action == "start":
        return await _mock_start(ctx, session_id, fields, payload["jd"], payload["level"])
    if action == "answer":
        return await _mock_answer(ctx, session_id, payload["answer"])
    return {"error": {"code": "QA_BAD_ACTION", "module": "mock_interview", "message": f"未知动作 {action}"}}


async def _mock_start(ctx, session_id: str, fields: dict, jd: str, level: str) -> dict:
    profile = LEVEL_MAP.get(level, LEVEL_MAP["中级"])
    difficulty_profile = {"tag": profile["tag"], "depth": profile["depth"], "ratio": DEFAULT_RATIO}

    await ctx.emitter.emit("生成面试问题")
    question_list = (await _run(generate_questions, fields, jd, difficulty_profile))["question_list"]
    all_questions = _flatten_questions(question_list)
    if not all_questions:
        return {"session_id": session_id, "status": "done", "report": None}

    current = dict(all_questions[0])
    current["type"] = "main"
    state = {
        "question_list": question_list,
        "all_questions": all_questions,
        "progress": {"asked": 1, "total": len(all_questions)},
        "qa_records": [],
        "current_question": current,
        "pending_follow_up": None,
    }
    await _run(_mock_set, session_id, state)

    return {
        "session_id": session_id,
        "current_question": current,
        "progress": state["progress"],
        "status": "asking",
    }


async def _mock_answer(ctx, session_id: str, user_answer: str) -> dict:
    if not user_answer:
        return {"error": {"code": "QA_NO_ANSWER", "module": "mock_interview", "message": "请先作答"}}

    state = await _run(_mock_get, session_id)
    if not state:
        return {"error": {"code": "QA_NO_SESSION", "module": "mock_interview", "message": "会话不存在，请重新开始"}}

    current = state.get("current_question") or {}
    question_text = current.get("question", "")
    await ctx.emitter.emit("评估回答")

    feedback = (await _run(evaluate_answer, question_text, user_answer))["feedback"]
    qa_records = list(state.get("qa_records") or [])
    qa_records.append({
        "question": question_text,
        "answer": user_answer,
        "score": feedback.get("score"),
        "category": current.get("category", ""),
    })
    state["qa_records"] = qa_records

    follow_up = feedback.get("follow_up", "")
    if current.get("type") == "main" and follow_up:
        next_q = {
            "id": current.get("id", ""),
            "question": follow_up,
            "category": current.get("category", ""),
            "type": "follow_up",
        }
        state["current_question"] = next_q
        state["pending_follow_up"] = follow_up
        await _run(_mock_set, session_id, state)
        return {"session_id": session_id, "feedback": feedback, "current_question": next_q, "status": "asking"}

    # 无追问：推进下一主问题或总结
    progress = state.get("progress") or {}
    asked = progress.get("asked", 0)
    total = progress.get("total", 0)
    all_questions = state.get("all_questions") or []

    if asked >= total:
        report = await _run(summarize_report, qa_records)
        report["qa_records"] = qa_records
        state["report"] = report
        await _run(_mock_set, session_id, state)
        return {"session_id": session_id, "feedback": feedback, "report": report, "status": "done"}

    current = dict(all_questions[asked])
    current["type"] = "main"
    progress["asked"] = asked + 1
    state["current_question"] = current
    state["pending_follow_up"] = None
    await _run(_mock_set, session_id, state)

    return {
        "session_id": session_id,
        "feedback": feedback,
        "current_question": current,
        "progress": progress,
        "status": "asking",
    }


def _mock_set(session_id: str, state: dict) -> None:
    _mock_client().set(f"{_MOCK_PREFIX}{session_id}", json.dumps(state, ensure_ascii=False))


def _mock_get(session_id: str) -> dict | None:
    raw = _mock_client().get(f"{_MOCK_PREFIX}{session_id}")
    return json.loads(raw) if raw else None


# ---------------------------------------------------------------------------
# 简历智能生成与优化
# ---------------------------------------------------------------------------

async def _handle_edit_generate(ctx, context: dict, user_id: str) -> dict:
    payload = build_edit_context(context)
    source = payload["fields"] or payload["manual_input"] or {}
    if not source:
        return {"error": {"code": "EDIT_EMPTY_RESUME", "module": "generate", "message": "简历内容为空，请先上传或输入"}}

    await ctx.emitter.emit("生成简历")
    generated = (await _run(generate_resume, source))["generated_resume"]

    resume_id = context.get("resume_id")
    if resume_id and await _run(repositories.get_resume_for_user, resume_id, user_id):
        await _run(repositories.update_resume_fields, resume_id, generated, None)
    else:
        resume_id = f"rsm_{uuid.uuid4().hex[:8]}"
        await _run(
            repositories.create_resume,
            resume_id, user_id, generated, [], name="智能生成简历", source_type="manual", ocr_used=False, file_hash="",
        )
        await _run(version_store.save, resume_id, "v1", generated, "generate")

    return {"resume_id": resume_id, "generated_resume": generated}


async def _handle_edit_optimize(ctx, context: dict, user_id: str) -> dict:
    payload = build_edit_context(context)
    fields = payload["fields"] or payload["manual_input"] or {}
    if not fields:
        return {"error": {"code": "EDIT_EMPTY_RESUME", "module": "optimize", "message": "简历内容为空"}}

    await ctx.emitter.emit("生成优化建议")
    suggestions = await _run(
        optimize_skills, fields, payload["jd"], payload["optimize_types"]
    )
    return {"resume_id": context.get("resume_id"), "suggestions": suggestions}


async def _handle_edit_apply(ctx, context: dict, user_id: str) -> dict:
    payload = build_edit_context(context)
    fields = payload["fields"]
    suggestions = payload["suggestions"] or []
    if not fields:
        return {"error": {"code": "EDIT_EMPTY_RESUME", "module": "apply", "message": "简历内容为空"}}
    if not suggestions:
        return {"error": {"code": "EDIT_NO_SUGGESTION", "module": "apply", "message": "没有可应用的优化建议"}}

    resume_id = context.get("resume_id") or f"rsm_{uuid.uuid4().hex[:8]}"
    await ctx.emitter.emit("应用优化建议")
    result = await _run(
        apply_suggestions, version_store, resume_id, fields, suggestions,
        payload["suggestion_ids"] or [], payload["accept_all"],
    )

    # 同步最新版本字段到 resumes 表
    latest = await _run(version_store.latest, resume_id)
    if latest:
        await _run(repositories.update_resume_fields, resume_id, latest["fields"], None)

    return {"resume_id": resume_id, **result}


async def _handle_edit_diff(ctx, context: dict, user_id: str) -> dict:
    payload = build_edit_context(context)
    resume_id = context.get("resume_id")
    version = payload["version"]
    if not resume_id or not version:
        return {"error": {"code": "EDIT_NO_VERSION", "module": "diff", "message": "请指定简历与版本号"}}

    diffs = await _run(diff_versions, version_store, resume_id, version, payload["base_version"])
    return {"resume_id": resume_id, "version": version, "diffs": diffs}
