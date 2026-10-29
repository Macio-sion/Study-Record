"""
用户 DAO
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user import User
from app.dao.base_dao import BaseDAO


class UserDAO(BaseDAO[User]):
    """用户数据访问对象"""

    def __init__(self):
        super().__init__(User)

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """按用户名查询"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def check_username_exists(self, db: AsyncSession, username: str, exclude_id: Optional[int] = None) -> bool:
        """检查用户名是否已存在"""
        query = select(User).where(User.username == username)
        if exclude_id is not None:
            query = query.where(User.id != exclude_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None


# 单例
user_dao = UserDAO()
