"""操作日志 Service"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.log_dao import log_dao
from app.model.user_log import UserLog
from app.dto.log_schema import LogResponse, LogPageQuery


async def write_log(db: AsyncSession, user_id: int, action: str, module: str, target_id: int = None, detail: str = None, ip_address: str = None):
    """写入操作日志"""
    log = UserLog(user_id=user_id, action=action, module=module, target_id=target_id, detail=detail, ip_address=ip_address)
    await log_dao.create(db, log)


async def list_logs(db: AsyncSession, query: LogPageQuery) -> tuple[list[LogResponse], int]:
    from sqlalchemy import or_
    filters = []
    if query.user_id:
        filters.append(UserLog.user_id == query.user_id)
    if query.module:
        filters.append(UserLog.module == query.module)
    if query.action:
        filters.append(UserLog.action == query.action)
    if query.start_time:
        filters.append(UserLog.created_at >= query.start_time)
    if query.end_time:
        filters.append(UserLog.created_at <= query.end_time)
    if hasattr(query, 'keyword') and query.keyword:
        filters.append(or_(
            UserLog.module.like(f"%{query.keyword}%"),
            UserLog.action.like(f"%{query.keyword}%"),
            UserLog.detail.like(f"%{query.keyword}%"),
        ))
    items, total = await log_dao.get_all(db, page=query.page, page_size=query.page_size, filters=filters, order_by=UserLog.id.desc())
    return [LogResponse.model_validate(l) for l in items], total
