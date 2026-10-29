"""成绩管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import get_current_user, require_role
from app.model.user import User
from app.dto.score_schema import ScoreCreate, ScoreUpdate, ScorePageQuery
from app.service import score_service

score_router = APIRouter(prefix="/api/scores", tags=["成绩管理"])


@score_router.get("", summary="成绩列表")
async def list_scores(page: int = 1, page_size: int = 20, student_id: int = None, course_id: int = None, semester_id: int = None, college_id: int = None, major_id: int = None, keyword: str = None, db: AsyncSession = Depends(get_db)):
    query = ScorePageQuery(page=page, page_size=page_size, student_id=student_id, course_id=course_id, semester_id=semester_id, college_id=college_id, major_id=major_id, keyword=keyword)
    items, total = await score_service.list_scores(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@score_router.post("", summary="录入成绩", dependencies=[Depends(require_role("teacher", "admin"))])
async def create_score(req: ScoreCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(data=await score_service.create_score(db, current_user.id, req))


@score_router.put("/{score_id}", summary="修改成绩", dependencies=[Depends(require_role("teacher", "admin"))])
async def update_score(score_id: int, req: ScoreUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(data=await score_service.update_score(db, current_user.id, score_id, req))


@score_router.get("/my", summary="我的成绩")
async def get_my_scores(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    semester_id: int = None,
    course_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.service.student_service import get_student_by_user_id
    student = await get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="未找到关联的学生档案")
    query = ScorePageQuery(page=page, page_size=page_size, student_id=student.id, semester_id=semester_id, course_id=course_id)
    items, total = await score_service.list_my_scores(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)
