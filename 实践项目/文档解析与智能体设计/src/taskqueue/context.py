"""上下文策略（Context Strategy）。

设计要点（对应《模式设计》2.3「统一 Agent 运行时」与 7「模块间打通」）：

1. **唯一数据源**：``StructuredResume.fields`` 由解析引擎唯一产出，落 PostgreSQL 的
   ``resumes.fields``（JSONB）。问答/优化两类下游任务只读这份数据，不重新解析文件。

2. **组装方式**：每个任务 handler 依据 ``task_type`` 从三类来源拼出初始状态：
   - 简历字段（PostgreSQL ``resumes`` 表，缺省回退版本存储）；
   - 请求参数（JD / level / question / optimize_types 等，经 Docket 队列传来）；
   - 会话记忆（Redis ``qa:session:{session_id}``，多轮问答上下文，敏感信息已脱敏）。

3. **置信度贯穿**：解析产出的 ``confidence`` 一路传递；低置信度/缺失字段进入
   ``pending``，先由用户在「待确认」环节修正，再进入下游问答/优化。

4. **可追溯**：优化模块的每次应用产出新版本（``resume_versions``），支持回退与对比。
"""

from __future__ import annotations

from db import repositories
from services.edit_engine.version import load_resume_fields as _load_from_versions
from services.qa_engine.memory import memory_store


def load_resume_fields(resume_id: str) -> dict:
    """加载简历字段（唯一数据源）：优先 PostgreSQL resumes 表，回退版本存储。"""
    if not resume_id:
        return {}
    resume = repositories.get_resume(resume_id)
    if resume and resume.get("fields"):
        return resume["fields"]
    return _load_from_versions(None, resume_id) or {}


def load_session_history(session_id: str) -> list:
    """加载多轮问答会话记忆（脱敏后），无则返回空列表。"""
    if not session_id:
        return []
    return memory_store.get(session_id)


def build_parse_context(payload: dict) -> dict:
    """解析任务上下文：需要 file_id（字节流由 handler 从 Redis 取回）。"""
    return {
        "file_id": payload.get("file_id"),
        "file_name": payload.get("file_name") or "resume",
    }


def build_coaching_context(payload: dict) -> dict:
    """面试辅导上下文：简历字段 + 提问 + 历史记忆。"""
    fields = load_resume_fields(payload.get("resume_id"))
    return {
        "resume_id": payload.get("resume_id"),
        "fields": fields,
        "question": payload.get("question"),
        "session_id": payload.get("session_id"),
        "history": load_session_history(payload.get("session_id")),
    }


def build_mock_interview_context(payload: dict) -> dict:
    """模拟面试上下文：简历字段 + JD + 难度级别。"""
    return {
        "resume_id": payload.get("resume_id"),
        "fields": load_resume_fields(payload.get("resume_id")),
        "jd": payload.get("jd") or "",
        "level": payload.get("level") or "中级",
        "action": payload.get("action") or "start",
        "answer": payload.get("answer") or "",
    }


def build_edit_context(payload: dict) -> dict:
    """生成/优化上下文：简历字段（或手动输入）+ JD + 优化类型。"""
    return {
        "resume_id": payload.get("resume_id"),
        "fields": load_resume_fields(payload.get("resume_id")),
        "manual_input": payload.get("manual_input"),
        "jd": payload.get("jd") or "",
        "optimize_types": payload.get("optimize_types"),
        "suggestions": payload.get("suggestions"),
        "suggestion_ids": payload.get("suggestion_ids"),
        "accept_all": payload.get("accept_all", False),
        "version": payload.get("version"),
        "base_version": payload.get("base_version"),
    }
