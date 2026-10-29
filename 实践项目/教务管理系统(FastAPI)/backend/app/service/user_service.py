"""
用户管理 Service
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.user_dao import user_dao
from app.model.user import User
from app.dto.user_schema import (
    UserCreate, UserUpdate, UserResponse, UserPageQuery, ChangePasswordRequest
)
from app.common.security import hash_password, verify_password
from app.common.exception import ConflictException, NotFoundException, BusinessException


async def create_user(db: AsyncSession, req: UserCreate) -> UserResponse:
    """创建用户"""
    if await user_dao.check_username_exists(db, req.username):
        raise ConflictException(f"用户名 '{req.username}' 已存在")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        real_name=req.real_name,
        role_code=req.role_code,
        phone=req.phone,
        email=req.email,
        is_active=req.is_active,
    )
    user = await user_dao.create(db, user)
    return UserResponse.model_validate(user)


async def update_user(db: AsyncSession, user_id: int, req: UserUpdate) -> UserResponse:
    """更新用户信息"""
    user = await user_dao.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException(f"用户不存在: id={user_id}")
    user = await user_dao.update(
        db, user,
        real_name=req.real_name,
        phone=req.phone,
        email=req.email,
        is_active=req.is_active,
    )
    return UserResponse.model_validate(user)


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """删除用户"""
    if not await user_dao.delete(db, user_id):
        raise NotFoundException(f"用户不存在: id={user_id}")
    return True


async def get_user(db: AsyncSession, user_id: int) -> UserResponse:
    """获取单个用户"""
    user = await user_dao.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException(f"用户不存在: id={user_id}")
    return UserResponse.model_validate(user)


async def list_users(db: AsyncSession, query: UserPageQuery) -> tuple[list[UserResponse], int]:
    """分页查询用户"""
    filters = []
    if query.keyword:
        from sqlalchemy import or_
        filters.append(
            or_(
                User.username.like(f"%{query.keyword}%"),
                User.real_name.like(f"%{query.keyword}%"),
            )
        )
    if query.role_code:
        filters.append(User.role_code == query.role_code)
    if query.is_active is not None:
        filters.append(User.is_active == query.is_active)

    items, total = await user_dao.get_all(
        db, page=query.page, page_size=query.page_size, filters=filters
    )
    return [UserResponse.model_validate(u) for u in items], total


async def change_password(
    db: AsyncSession, user_id: int, req: ChangePasswordRequest
) -> bool:
    """修改密码"""
    user = await user_dao.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException(f"用户不存在: id={user_id}")

    if not verify_password(req.old_password, user.password_hash):
        raise BusinessException(code=400, message="原密码错误")

    user.password_hash = hash_password(req.new_password)
    await db.flush()
    return True


async def get_current_user_info(db: AsyncSession, user_id: int) -> UserResponse:
    """获取当前登录用户信息"""
    user = await user_dao.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException(f"用户不存在: id={user_id}")
    return UserResponse.model_validate(user)
