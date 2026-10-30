"""Pydantic 请求/响应模型（REST 接口数据契约）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 统一响应包裹
# ---------------------------------------------------------------------------

class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any = None


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def err(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}


# ---------------------------------------------------------------------------
# 鉴权
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    account: str = Field(..., description="登录账号（手机号/邮箱/用户名）")
    password: str = Field(..., min_length=6, max_length=64)
    nickname: str = ""


class LoginRequest(BaseModel):
    account: str
    password: str


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar: str | None = None
    phone: str | None = None
    email: str | None = None
    job_intention: str | None = None


class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=64)


# ---------------------------------------------------------------------------
# 简历
# ---------------------------------------------------------------------------

class FieldConfirmation(BaseModel):
    field: str
    value: Any


class ConfirmFieldsRequest(BaseModel):
    confirmations: list[FieldConfirmation]


# ---------------------------------------------------------------------------
# 任务
# ---------------------------------------------------------------------------

class CreateTaskRequest(BaseModel):
    task_type: str = Field(..., description="parse / coaching / mock_interview / edit.generate / edit.optimize / edit.apply / edit.diff")
    message: str = ""
    resume_id: str | None = None
    file_id: str | None = None
    file_name: str | None = None
    question: str | None = None
    session_id: str | None = None
    jd: str | None = None
    level: str | None = None
    optimize_types: list[str] | None = None
    suggestions: list[dict] | None = None
    suggestion_ids: list[str] | None = None
    accept_all: bool = False
    version: str | None = None
    base_version: str | None = None
    manual_input: dict | None = None
    # mock_interview 交互字段
    action: str | None = None
    answer: str | None = None


# ---------------------------------------------------------------------------
# 求职记录
# ---------------------------------------------------------------------------

class CreateJobRequest(BaseModel):
    company: str
    position: str = ""
    status: str = "待投递"
    date: str | None = None
    note: str = ""


class UpdateJobRequest(BaseModel):
    company: str | None = None
    position: str | None = None
    status: str | None = None
    date: str | None = None
    note: str | None = None


# ---------------------------------------------------------------------------
# 反馈
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    content: str
    screenshot: str = ""
