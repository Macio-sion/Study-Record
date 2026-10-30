"""用户中心路由：个人信息 / 改密 / 导出 / 删除 / 统计 / 反馈。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api import security
from api.deps import CurrentUser
from api.schemas import (
    FeedbackRequest,
    UpdatePasswordRequest,
    UpdateProfileRequest,
    ok,
)
from db import repositories

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _public(user: dict) -> dict:
    """剔除敏感字段（password_hash）后的用户信息。"""
    if not user:
        return None
    return {
        "id": user["id"],
        "account": user["account"],
        "nickname": user["nickname"],
        "avatar": user["avatar"],
        "phone": user["phone"],
        "email": user["email"],
        "job_intention": user["job_intention"],
    }


@router.get("/me")
def get_me(user_id: str = CurrentUser):
    user = repositories.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ok(_public(user))


@router.patch("/me")
def update_me(body: UpdateProfileRequest, user_id: str = CurrentUser):
    repositories.update_user(
        user_id,
        nickname=body.nickname,
        avatar=body.avatar,
        phone=body.phone,
        email=body.email,
        job_intention=body.job_intention,
    )
    user = repositories.get_user(user_id)
    return ok(_public(user))


@router.put("/me/password")
def change_password(body: UpdatePasswordRequest, user_id: str = CurrentUser):
    user = repositories.get_user(user_id)
    if not user or not security.verify_password(body.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="原密码错误")
    repositories.update_password(user_id, security.hash_password(body.new_password))
    return ok({"success": True})


@router.get("/me/stats")
def get_stats(user_id: str = CurrentUser):
    return ok({"stats": repositories.usage_stats(user_id)})


@router.post("/me/export")
def export_data(user_id: str = CurrentUser):
    """导出全部简历数据（JSON）。"""
    resumes = repositories.list_resumes(user_id, page=1, page_size=1000)
    jobs = repositories.list_jobs(user_id, page=1, page_size=1000)
    user = repositories.get_user(user_id)
    public_user = {k: user[k] for k in ("id", "account", "nickname", "avatar", "phone", "email", "job_intention")} if user else None
    payload = {
        "user": public_user,
        "resumes": resumes["list"],
        "jobs": jobs["list"],
    }
    return ok(payload)


@router.delete("/me/data")
def delete_data(user_id: str = CurrentUser):
    """一键删除全部简历/版本/求职记录数据。"""
    resumes = repositories.list_resumes(user_id, page=1, page_size=1000)
    for r in resumes["list"]:
        repositories.delete_resume(r["id"])
    jobs = repositories.list_jobs(user_id, page=1, page_size=1000)
    for j in jobs["list"]:
        repositories.delete_job(j["id"])
    return ok({"deleted": True})


# ---------------------------------------------------------------------------
# 反馈（挂在用户中心下）
# ---------------------------------------------------------------------------

feedback_router = APIRouter(prefix="/api/v1", tags=["feedback"])


@feedback_router.post("/feedback")
def submit_feedback(body: FeedbackRequest, user_id: str = CurrentUser):
    result = repositories.create_feedback(user_id, body.content, body.screenshot)
    return ok(result)
