"""教师管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role, get_current_user
from app.dto.teacher_schema import TeacherCreate, TeacherUpdate, TeacherPageQuery
from app.service import teacher_service

teacher_router = APIRouter(prefix="/api/teachers", tags=["教师管理"])

@teacher_router.get("", summary="教师列表")
async def list_teachers(page: int = 1, page_size: int = 20, college_id: int = None, keyword: str = None, db: AsyncSession = Depends(get_db)):
    query = TeacherPageQuery(page=page, page_size=page_size, college_id=college_id, keyword=keyword)
    items, total = await teacher_service.list_teachers(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@teacher_router.get("/me", summary="获取当前教师档案")
async def get_my_teacher(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """根据当前登录用户的 user_id 获取教师档案"""
    from app.service.teacher_service import get_teacher_by_user_id
    from app.dto.teacher_schema import TeacherResponse
    teacher = await get_teacher_by_user_id(db, current_user.id)
    if not teacher:
        raise HTTPException(status_code=404, detail="未找到关联的教师档案")
    return success(data=TeacherResponse.model_validate(teacher))


@teacher_router.get("/{teacher_id}", summary="教师详情")
async def get_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await teacher_service.get_teacher(db, teacher_id))

@teacher_router.post("", summary="创建教师", dependencies=[Depends(require_role("admin"))])
async def create_teacher(req: TeacherCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await teacher_service.create_teacher(db, req))

@teacher_router.put("/{teacher_id}", summary="更新教师", dependencies=[Depends(require_role("admin"))])
async def update_teacher(teacher_id: int, req: TeacherUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await teacher_service.update_teacher(db, teacher_id, req))

@teacher_router.delete("/{teacher_id}", summary="删除教师", dependencies=[Depends(require_role("admin"))])
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    await teacher_service.delete_teacher(db, teacher_id)
    return success(message="删除成功")
