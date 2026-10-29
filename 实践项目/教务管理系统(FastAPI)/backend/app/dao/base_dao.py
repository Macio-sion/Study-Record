"""
通用 DAO 基类
提供基础的 CRUD 操作
"""
from typing import Any, Optional, Sequence, TypeVar, Generic, Type

from sqlalchemy import Select, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.model.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseDAO(Generic[ModelType]):
    """通用数据访问对象基类"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """按主键查询"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[list] = None,
        order_by: Optional[Any] = None,
    ) -> tuple[list[ModelType], int]:
        """
        分页查询

        Returns:
            (数据列表, 总记录数)
        """
        query = select(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            query = query.order_by(self.model.id.desc())

        # 总数
        count_query = select(func.count()).select_from(self.model)
        if filters:
            for f in filters:
                count_query = count_query.where(f)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create(self, db: AsyncSession, obj: ModelType) -> ModelType:
        """新增记录"""
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, obj: ModelType, **kwargs) -> ModelType:
        """更新记录"""
        for key, value in kwargs.items():
            if hasattr(obj, key) and value is not None:
                setattr(obj, key, value)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """删除记录"""
        result = await db.execute(delete(self.model).where(self.model.id == id))
        await db.flush()
        return result.rowcount > 0

    async def count(self, db: AsyncSession, filters: Optional[list] = None) -> int:
        """计数"""
        query = select(func.count()).select_from(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        result = await db.execute(query)
        return result.scalar() or 0
