"""鉴权路由：注册 / 登录 / 登出。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from api import security
from api.schemas import LoginRequest, RegisterRequest, ok
from db import repositories

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
def register(body: RegisterRequest):
    if repositories.get_user_by_account(body.account):
        raise HTTPException(status_code=409, detail="该账号已注册")

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    user = repositories.create_user(
        user_id=user_id,
        account=body.account,
        password_hash=security.hash_password(body.password),
        nickname=body.nickname or body.account,
    )
    token = security.create_access_token(user_id, body.account)
    return ok({"token": token, "user": _public(user)})


@router.post("/login")
def login(body: LoginRequest):
    user = repositories.get_user_by_account(body.account)
    if not user or not security.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = security.create_access_token(user["id"], user["account"])
    return ok({"token": token, "user": _public(user)})


@router.post("/logout")
def logout():
    # JWT 无状态，登出由前端清除 token 即可。
    return ok({"success": True})


def _public(user: dict) -> dict:
    return {
        "id": user["id"],
        "account": user["account"],
        "nickname": user["nickname"],
        "avatar": user["avatar"],
        "phone": user["phone"],
        "email": user["email"],
        "job_intention": user["job_intention"],
    }
