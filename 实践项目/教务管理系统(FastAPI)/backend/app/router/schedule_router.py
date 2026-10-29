"""排课管理路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role
from app.dto.schedule_schema import ScheduleCreate, ScheduleUpdate, SchedulePageQuery
from app.service import schedule_service

schedule_router = APIRouter(prefix="/api/schedules", tags=["排课管理"])


@schedule_router.get("", summary="排课列表")
async def list_schedules(page: int = 1, page_size: int = 20, semester_id: int = None, teacher_id: int = None, classroom_id: int = None, db: AsyncSession = Depends(get_db)):
    query = SchedulePageQuery(page=page, page_size=page_size, semester_id=semester_id, teacher_id=teacher_id, classroom_id=classroom_id)
    items, total = await schedule_service.list_schedules(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@schedule_router.get("/{schedule_id}", summary="排课详情")
async def get_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await schedule_service.get_schedule(db, schedule_id))


@schedule_router.post("", summary="创建排课", dependencies=[Depends(require_role("admin"))])
async def create_schedule(req: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await schedule_service.create_schedule(db, req))


@schedule_router.put("/{schedule_id}", summary="更新排课", dependencies=[Depends(require_role("admin"))])
async def update_schedule(schedule_id: int, req: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await schedule_service.update_schedule(db, schedule_id, req))


@schedule_router.delete("/{schedule_id}", summary="删除排课", dependencies=[Depends(require_role("admin"))])
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    await schedule_service.delete_schedule(db, schedule_id)
    return success(message="删除成功")
