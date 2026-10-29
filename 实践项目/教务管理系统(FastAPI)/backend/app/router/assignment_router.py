"""作业管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role, get_current_user
from app.dto.assignment_schema import AssignmentCreate, AssignmentUpdate, AssignmentPageQuery, SubmissionCreate, SubmissionReview
from app.service import assignment_service

assignment_router = APIRouter(prefix="/api/assignments", tags=["作业管理"])


@assignment_router.get("/my", summary="我的作业列表")
async def get_my_assignments(
    page: int = 1, page_size: int = 20,
    course_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """学生查看自己所选课程的所有作业，含提交状态"""
    from app.service.student_service import get_student_by_user_id
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    items, total = await assignment_service.list_my_assignments(db, student.id, page, page_size, course_id)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@assignment_router.get("", summary="作业列表")
async def list_assignments(
    page: int = 1, page_size: int = 20,
    course_id: int = None, keyword: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 教师角色：仅查看自己所授课程的作业
    teacher_id = None
    if current_user.role_code == "teacher":
        from app.service.teacher_service import get_teacher_by_user_id
        teacher = await get_teacher_by_user_id(db, current_user.id)
        if not teacher:
            raise HTTPException(status_code=404, detail="未找到关联的教师档案")
        teacher_id = teacher.id

    query = AssignmentPageQuery(page=page, page_size=page_size, course_id=course_id, keyword=keyword)
    items, total = await assignment_service.list_assignments(db, query, teacher_id=teacher_id)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@assignment_router.get("/{assignment_id}", summary="作业详情")
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await assignment_service.get_assignment(db, assignment_id))


@assignment_router.post("", summary="发布作业", dependencies=[Depends(require_role("teacher", "admin"))])
async def create_assignment(
    req: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 教师角色：自动从 token 解析 teacher_id
    if current_user.role_code != "admin":
        from app.service.teacher_service import get_teacher_by_user_id
        teacher = await get_teacher_by_user_id(db, current_user.id)
        if not teacher:
            raise HTTPException(status_code=404, detail="未找到关联的教师档案")
        req.teacher_id = teacher.id
    return success(data=await assignment_service.create_assignment(db, req))


@assignment_router.put("/{assignment_id}", summary="更新作业", dependencies=[Depends(require_role("admin"))])
async def update_assignment(assignment_id: int, req: AssignmentUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await assignment_service.update_assignment(db, assignment_id, req))


@assignment_router.delete("/{assignment_id}", summary="删除作业", dependencies=[Depends(require_role("admin"))])
async def delete_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    await assignment_service.delete_assignment(db, assignment_id)
    return success(message="删除成功")


# 提交
@assignment_router.post("/{assignment_id}/submit", summary="提交作业")
async def submit_assignment(
    assignment_id: int,
    req: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Auto-resolve student_id from current user
    from app.service.student_service import get_student_by_user_id
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    req.student_id = student.id
    req.assignment_id = assignment_id
    return success(data=await assignment_service.submit_assignment(db, req))


@assignment_router.get("/{assignment_id}/submissions", summary="作业提交列表")
async def list_submissions(assignment_id: int, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db)):
    items, total = await assignment_service.list_submissions(db, assignment_id, page, page_size)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@assignment_router.put("/submissions/{submission_id}/review", summary="批阅作业", dependencies=[Depends(require_role("teacher", "admin"))])
async def review_submission(submission_id: int, req: SubmissionReview, db: AsyncSession = Depends(get_db)):
    return success(data=await assignment_service.review_submission(db, submission_id, req))


@assignment_router.put("/submissions/{submission_id}", summary="修改提交作业")
async def update_submission(
    submission_id: int,
    req: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """学生修改已提交但未批改的作业内容（修改申请）"""
    from app.service.student_service import get_student_by_user_id
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    return success(data=await assignment_service.update_my_submission(db, submission_id, student.id, req))
