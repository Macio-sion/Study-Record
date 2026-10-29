"""选课管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role, get_current_user
from app.dto.selection_schema import CourseSelectionCreate, SelectionPageQuery
from app.service import selection_service

selection_router = APIRouter(prefix="/api/selections", tags=["选课管理"])


@selection_router.get("", summary="选课记录列表")
async def list_selections(
    page: int = 1, page_size: int = 20,
    student_id: int = None, course_id: int = None, semester_id: int = None,
    college_id: int = None, major_id: int = None, status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 学生角色自动过滤为本人
    from app.service.student_service import get_student_by_user_id
    if current_user.role_code == 'student':
        student = await get_student_by_user_id(db, current_user.id)
        if student:
            student_id = student.id
    query = SelectionPageQuery(page=page, page_size=page_size, student_id=student_id, course_id=course_id, semester_id=semester_id, college_id=college_id, major_id=major_id, status=status)
    items, total = await selection_service.list_selections(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@selection_router.get("/{selection_id}", summary="选课详情")
async def get_selection(selection_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await selection_service.get_selection(db, selection_id))


@selection_router.post("", summary="选课（高并发安全）", dependencies=[Depends(require_role("student"))])
async def select_course(req: CourseSelectionCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    # 自动填充 student_id 和 semester_id
    from app.service.student_service import get_student_by_user_id
    from app.model.semester import Semester
    from sqlalchemy import select
    if not req.student_id:
        student = await get_student_by_user_id(db, current_user.id)
        if not student:
            raise HTTPException(status_code=404, detail="未找到关联的学生档案")
        req.student_id = student.id
    if not req.semester_id:
        semester = (await db.execute(select(Semester).where(Semester.is_current == True))).scalar_one_or_none()
        if not semester:
            raise HTTPException(status_code=400, detail="无当前学期")
        req.semester_id = semester.id
    return success(data=await selection_service.select_course(db, req))


@selection_router.put("/{selection_id}/drop", summary="退课")
async def drop_course(selection_id: int, db: AsyncSession = Depends(get_db)):
    await selection_service.drop_course(db, selection_id)
    return success(message="退课成功")
