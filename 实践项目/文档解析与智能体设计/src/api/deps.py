"""FastAPI 依赖：JWT 鉴权取当前用户。"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from api.security import decode_access_token


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """从 ``Authorization: Bearer <token>`` 解析当前用户 ID。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return payload["sub"]


CurrentUser = Depends(get_current_user_id)
