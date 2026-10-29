"""
RBAC 权限控制
- JWT Token 依赖注入
- 角色权限检查
"""
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.common.security import decode_access_token
from app.common.exception import UnauthorizedException, ForbiddenException
from app.model.user import User

# HTTP Bearer Token 提取器
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从请求头中提取 JWT Token 并解析当前用户
    
    Returns:
        当前登录的 User 对象
    Raises:
        UnauthorizedException: Token 无效或用户不存在
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException("Token无效或已过期")

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedException("Token中缺少用户标识")
    user_id = int(user_id_str)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedException("用户不存在")
    if not user.is_active:
        raise ForbiddenException("用户已被禁用")

    return user


def require_role(*roles: str):
    """
    角色权限检查工厂函数
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            pass
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_code not in roles:
            raise ForbiddenException(f"需要以下角色之一: {', '.join(roles)}")
        return current_user

    return role_checker
