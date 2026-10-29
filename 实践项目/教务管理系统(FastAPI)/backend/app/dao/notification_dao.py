"""消息通知 DAO"""
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.user_notification import UserNotification


async def get_notifications(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20, is_read: bool = None) -> tuple[list[UserNotification], int]:
    """获取用户通知列表"""
    stmt = select(UserNotification).where(UserNotification.user_id == user_id)
    if is_read is not None:
        stmt = stmt.where(UserNotification.is_read == is_read)
    stmt = stmt.order_by(UserNotification.created_at.desc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return list(items), total


async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    """获取未读通知数量"""
    stmt = select(func.count()).select_from(UserNotification).where(
        UserNotification.user_id == user_id,
        UserNotification.is_read == False,
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def mark_as_read(db: AsyncSession, notification_id: int, user_id: int) -> bool:
    """标记通知为已读"""
    stmt = (
        update(UserNotification)
        .where(UserNotification.id == notification_id, UserNotification.user_id == user_id)
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount > 0


async def mark_all_read(db: AsyncSession, user_id: int) -> int:
    """标记所有通知为已读"""
    stmt = (
        update(UserNotification)
        .where(UserNotification.user_id == user_id, UserNotification.is_read == False)
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount


async def create_notification(db: AsyncSession, user_id: int, title: str, content: str = None,
                              notification_type: str = 'system', related_url: str = None) -> UserNotification:
    """创建通知"""
    notif = UserNotification(
        user_id=user_id, title=title, content=content,
        notification_type=notification_type, related_url=related_url,
    )
    db.add(notif)
    await db.flush()
    await db.refresh(notif)
    return notif
