"""操作日志路由"""
from fastapi import APIRouter, Depends, Query
from app.common.response import success_page
from app.common.permission import get_current_user, require_role
from app.dto.log_schema import LogPageQuery
from app.service import log_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

log_router = APIRouter(prefix="/api/logs", tags=["操作日志"])


@log_router.get("", summary="分页查询操作日志")
async def list(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    user_id: int = None, module: str = None, action: str = None, keyword: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    query = LogPageQuery(page=page, page_size=page_size, user_id=user_id, module=module, action=action, keyword=keyword)
    items, total = await log_service.list_logs(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)
