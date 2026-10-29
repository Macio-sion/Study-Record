"""
认证 Service
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.user_dao import user_dao
from app.dto.user_schema import LoginRequest, LoginResponse
from app.common.security import verify_password, create_access_token
from app.common.exception import UnauthorizedException


async def login(db: AsyncSession, req: LoginRequest) -> LoginResponse:
    """
    用户登录

    Args:
        db: 数据库会话
        req: 登录请求

    Returns:
        LoginResponse: 含 JWT Token 的登录响应

    Raises:
        UnauthorizedException: 用户名或密码错误、用户被禁用
    """
    user = await user_dao.get_by_username(db, req.username)
    if user is None:
        raise UnauthorizedException("用户名或密码错误")

    if not verify_password(req.password, user.password_hash):
        raise UnauthorizedException("用户名或密码错误")

    if not user.is_active:
        raise UnauthorizedException("账户已被禁用，请联系管理员")

    # 创建 Token
    token_data = {"sub": str(user.id), "username": user.username, "role": user.role_code}
    token = create_access_token(token_data)

    return LoginResponse(
        token=token,
        username=user.username,
        real_name=user.real_name,
        role_code=user.role_code,
        user_id=user.id,
        managed_college_id=user.managed_college_id,
    )
