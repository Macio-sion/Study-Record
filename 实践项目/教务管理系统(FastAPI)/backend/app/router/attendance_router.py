"""考勤管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role, get_current_user
from app.dto.attendance_schema import AttendanceCreate, AttendanceUpdate, AttendancePageQuery
from app.service import attendance_service

attendance_router = APIRouter(prefix="/api/attendance", tags=["考勤管理"])


@attendance_router.get("/stats/by-teacher", summary="教师各课程考勤统计")
async def get_teacher_stats(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """获取当前教师所授各课程的出勤统计（用于条形图）"""
    from app.service.teacher_service import get_teacher_by_user_id
    teacher = await get_teacher_by_user_id(db, current_user.id)
    if not teacher:
        raise HTTPException(status_code=404, detail="未找到关联的教师档案")
    return success(data=await attendance_service.get_teacher_course_stats(db, teacher.id))


@attendance_router.get("/stats/courses", summary="多课程考勤统计")
async def get_courses_stats(course_ids: str = Query(..., description="逗号分隔的课程ID"), db: AsyncSession = Depends(get_db)):
    """获取指定课程的出勤统计（用于条形图）"""
    ids = [int(cid) for cid in course_ids.split(",") if cid.strip().isdigit()]
    return success(data=await attendance_service.get_courses_stats(db, ids))


@attendance_router.get("/stats", summary="考勤统计")
async def get_stats(course_id: int = None, student_id: int = None, db: AsyncSession = Depends(get_db)):
    """获取考勤统计（出勤率、缺勤数等）"""
    return success(data=await attendance_service.get_attendance_stats(db, course_id, student_id))


@attendance_router.get("", summary="考勤记录列表")
async def list_attendance(page: int = 1, page_size: int = 20, course_id: int = None, student_id: int = None, date: str = None, status: str = None, db: AsyncSession = Depends(get_db)):
    from datetime import date as date_type
    d = date_type.fromisoformat(date) if date else None
    query = AttendancePageQuery(page=page, page_size=page_size, course_id=course_id, student_id=student_id, date=d, status=status)
    items, total = await attendance_service.list_attendance(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@attendance_router.get("/my", summary="我的考勤记录")
async def get_my_attendance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course_id: int = None,
    date: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.service.student_service import get_student_by_user_id
    from datetime import date as date_type
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    d = date_type.fromisoformat(date) if date else None
    query = AttendancePageQuery(page=page, page_size=page_size, student_id=student.id, course_id=course_id, date=d, status=status)
    items, total = await attendance_service.list_my_attendance(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@attendance_router.get("/my/stats", summary="我的考勤统计")
async def get_my_attendance_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.service.student_service import get_student_by_user_id
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    return success(data=await attendance_service.get_attendance_stats(db, student_id=student.id))


@attendance_router.get("/{attendance_id}", summary="考勤详情")
async def get_attendance(attendance_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await attendance_service.get_attendance(db, attendance_id))


@attendance_router.post("", summary="创建考勤记录", dependencies=[Depends(require_role("teacher", "admin"))])
async def create_attendance(req: AttendanceCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await attendance_service.create_attendance(db, req))


@attendance_router.post("/batch", summary="批量考勤", dependencies=[Depends(require_role("teacher", "admin"))])
async def batch_attendance(records: list[AttendanceCreate], db: AsyncSession = Depends(get_db)):
    return success(data=await attendance_service.batch_create_attendance(db, records))


@attendance_router.put("/{attendance_id}", summary="更新考勤", dependencies=[Depends(require_role("teacher", "admin"))])
async def update_attendance(attendance_id: int, req: AttendanceUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await attendance_service.update_attendance(db, attendance_id, req))


@attendance_router.delete("/{attendance_id}", summary="删除考勤记录", dependencies=[Depends(require_role("admin"))])
async def delete_attendance(attendance_id: int, db: AsyncSession = Depends(get_db)):
    await attendance_service.delete_attendance(db, attendance_id)
    return success(message="删除成功")
