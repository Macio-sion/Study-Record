"""
认证路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.common.response import success
from app.dto.user_schema import LoginRequest
from app.service.auth_service import login

auth_router = APIRouter(prefix="/api/auth", tags=["认证管理"])


@auth_router.post("/login", summary="用户登录")
async def login_endpoint(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录，返回 JWT Token"""
    result = await login(db, req)
    return success(data=result.model_dump())
