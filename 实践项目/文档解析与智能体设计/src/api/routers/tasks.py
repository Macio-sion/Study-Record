"""任务路由：提交任务到 Redis 队列 + 轮询结果。

这是前端与 Redis 任务队列的对接层：
- ``POST /api/v1/tasks``  提交任务（JWT 鉴权，注入 user_id 到 caller/context）
- ``GET  /api/v1/tasks/{id}`` 轮询任务状态与结果

底层队列由 ``redis_agent_kit.AgentKit`` + Docket 管理，worker 侧消费见 ``queue/handlers.py``。
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from api.deps import CurrentUser
from api.schemas import CreateTaskRequest, ok
from db import repositories
from redis_agent_kit.models import Caller, CallerType

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _kit(request: Request):
    kit = getattr(request.app.state, "kit", None)
    if kit is None:
        raise HTTPException(status_code=500, detail="任务队列未初始化")
    return kit


@router.post("")
async def create_task(body: CreateTaskRequest, request: Request, user_id: str = CurrentUser):
    kit = _kit(request)

    # 组装任务上下文（结构化参数经 Docket 序列化传递，不塞大文件）
    context = {
        "user_id": user_id,
        "task_type": body.task_type,
        "resume_id": body.resume_id,
        "file_id": body.file_id,
        "file_name": body.file_name,
        "question": body.question,
        "session_id": body.session_id,
        "jd": body.jd,
        "level": body.level,
        "optimize_types": body.optimize_types,
        "suggestions": body.suggestions,
        "suggestion_ids": body.suggestion_ids,
        "accept_all": body.accept_all,
        "version": body.version,
        "base_version": body.base_version,
        "manual_input": body.manual_input,
        "action": body.action,
        "answer": body.answer,
    }
    # 清理 None，保持 context 干净
    context = {k: v for k, v in context.items() if v is not None}

    message = body.message or body.task_type
    try:
        result = await kit.create_and_submit_task(
            message=message,
            context=context,
            session_id=body.session_id,
            caller=Caller(type=CallerType.HUMAN, id=user_id),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 记录任务日志（用于使用统计）
    await asyncio.to_thread(
        repositories.log_task,
        result["task_id"], user_id, body.task_type, body.resume_id, "queued",
    )

    return ok({
        "task_id": result["task_id"],
        "session_id": result.get("session_id"),
        "status": "queued",
    })


@router.get("/{task_id}")
async def get_task(task_id: str, request: Request, user_id: str = CurrentUser):
    kit = _kit(request)
    task = await kit.task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return ok({
        "task_id": task.task_id,
        "status": task.status.value,
        "result": task.result,
        "error": task.error_message,
        "updates": [u.model_dump() for u in task.updates],
        "created_at": task.created_at.isoformat() if task.created_at else None,
    })
