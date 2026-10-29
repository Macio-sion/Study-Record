"""请假审批路由"""
from fastapi import APIRouter, Depends, Query
from app.common.response import success, success_page
from app.common.permission import get_current_user, require_role
from app.dto.leave_schema import LeaveCreate, LeaveUpdate, LeavePageQuery
from app.service import leave_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

leave_router = APIRouter(prefix="/api/leaves", tags=["请假管理"])


@leave_router.post("", summary="学生提交请假申请")
async def create(
    req: LeaveCreate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    result = await leave_service.create_leave(db, current_user.id, req)
    return success(data=result)


@leave_router.put("/{leave_id}/teacher", summary="教师审批（第一级）")
async def approve_teacher(
    leave_id: int, req: LeaveUpdate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    result = await leave_service.approve_teacher(db, leave_id, current_user.id, req)
    return success(data=result)


@leave_router.put("/{leave_id}/staff", summary="学工处审批（第二级）")
async def approve_staff(
    leave_id: int, req: LeaveUpdate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("academic_staff")),
):
    result = await leave_service.approve_staff(db, leave_id, current_user.id, req)
    return success(data=result)


@leave_router.put("/{leave_id}/cancel", summary="学生撤销请假申请")
async def cancel(
    leave_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    result = await leave_service.cancel_leave(db, leave_id, current_user.id)
    return success(data=result, message="已撤销")


@leave_router.get("/{leave_id}", summary="查询请假详情")
async def get(leave_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await leave_service.get_leave(db, leave_id)
    return success(data=result)


@leave_router.get("", summary="分页查询请假列表")
async def list(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    student_id: int = None, course_id: int = None,
    status: str = None, teacher_id: int = None, keyword: str = None,
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),
):
    # 学生角色自动过滤自己的请假记录
    if current_user.role_code == 'student' and not student_id:
        from app.service.leave_service import _get_student_by_user_id
        student = await _get_student_by_user_id(db, current_user.id)
        student_id = student.id

    # 教师角色：仅查看自己所教课程中学生的请假
    teacher_id_filter = teacher_id
    if current_user.role_code == 'teacher':
        from app.service.leave_service import _get_teacher_by_user_id
        t = await _get_teacher_by_user_id(db, current_user.id)
        teacher_id_filter = t.id

    query = LeavePageQuery(page=page, page_size=page_size, student_id=student_id, course_id=course_id, status=status, teacher_id=teacher_id, keyword=keyword)
    items, total = await leave_service.list_leaves(db, query, teacher_id=teacher_id_filter)
    return success_page(items=items, total=total, page=page, page_size=page_size)
