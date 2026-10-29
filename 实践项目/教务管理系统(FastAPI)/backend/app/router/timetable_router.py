"""课表路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success
from app.service import timetable_service

timetable_router = APIRouter(prefix="/api/timetable", tags=["课表系统"])


@timetable_router.get("/student/{student_id}", summary="学生课表")
async def student_timetable(student_id: int, semester_id: int, db: AsyncSession = Depends(get_db)):
    """查询学生课表"""
    data = await timetable_service.get_student_timetable(db, student_id, semester_id)
    return success(data=data)


@timetable_router.get("/teacher/{teacher_id}", summary="教师课表")
async def teacher_timetable(teacher_id: int, semester_id: int, db: AsyncSession = Depends(get_db)):
    """查询教师课表"""
    data = await timetable_service.get_teacher_timetable(db, teacher_id, semester_id)
    return success(data=data)


@timetable_router.get("/all", summary="全部课表（管理员）")
async def all_timetable(semester_id: int, week: int = None, db: AsyncSession = Depends(get_db)):
    """管理员查看全部课表，可按周筛选"""
    data = await timetable_service.get_all_timetable(db, semester_id, week)
    return success(data=data)
