"""用户消息通知路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.response import success, success_page
from app.common.permission import get_current_user
from app.dto.notification_schema import NotificationResponse, NotificationPageQuery
from app.dao import notification_dao
from app.database import get_db

notification_router = APIRouter(prefix="/api/notifications", tags=["消息通知"])


@notification_router.get("/unread-count", summary="获取未读通知数量")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = await notification_dao.get_unread_count(db, current_user.id)
    return success(data={"count": count})


@notification_router.get("", summary="获取通知列表")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: bool = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items, total = await notification_dao.get_notifications(db, current_user.id, page, page_size, is_read)
    return success_page(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total, page=page, page_size=page_size,
    )


@notification_router.put("/{notification_id}/read", summary="标记通知为已读")
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ok = await notification_dao.mark_as_read(db, notification_id, current_user.id)
    if not ok:
        return success(message="通知不存在")
    return success(message="已标记为已读")


@notification_router.put("/read-all", summary="标记所有通知为已读")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = await notification_dao.mark_all_read(db, current_user.id)
    return success(data={"count": count}, message=f"已标记 {count} 条通知为已读")
