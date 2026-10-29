"""
学院与专业管理路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role, get_current_user
from app.dto.college_schema import CollegeCreate, CollegeUpdate, CollegePageQuery, CollegeOverviewResponse
from app.dto.major_schema import MajorCreate, MajorUpdate, MajorPageQuery
from app.service import college_service

router = APIRouter(prefix="/api", tags=["学院与专业管理"])


# ========== 学院 ==========

@router.get("/colleges/all", summary="获取所有学院")
async def get_all_colleges(db: AsyncSession = Depends(get_db)):
    """获取所有学院（下拉选择用）"""
    items = await college_service.get_all_colleges(db)
    return success(data=items)


@router.get("/colleges", summary="学院列表")
async def list_colleges(
    page: int = 1, page_size: int = 20, keyword: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = CollegePageQuery(page=page, page_size=page_size, keyword=keyword)
    items, total = await college_service.list_colleges(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@router.get("/colleges/{college_id}", summary="学院详情")
async def get_college(college_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await college_service.get_college(db, college_id))


@router.post("/colleges", summary="创建学院", dependencies=[Depends(require_role("admin"))])
async def create_college(req: CollegeCreate, db: AsyncSession = Depends(get_db)):
    item = await college_service.create_college(db, req)
    return success(data=item)


@router.put("/colleges/{college_id}", summary="更新学院", dependencies=[Depends(require_role("admin"))])
async def update_college(college_id: int, req: CollegeUpdate, db: AsyncSession = Depends(get_db)):
    item = await college_service.update_college(db, college_id, req)
    return success(data=item)


@router.delete("/colleges/{college_id}", summary="删除学院", dependencies=[Depends(require_role("admin"))])
async def delete_college(college_id: int, db: AsyncSession = Depends(get_db)):
    await college_service.delete_college(db, college_id)
    return success(message="删除成功")


# ========== 专业 ==========

@router.get("/majors", summary="专业列表")
async def list_majors(
    page: int = 1, page_size: int = 20, college_id: int = None, keyword: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = MajorPageQuery(page=page, page_size=page_size, college_id=college_id, keyword=keyword)
    items, total = await college_service.list_majors(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@router.get("/majors/{major_id}", summary="专业详情")
async def get_major(major_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await college_service.get_major(db, major_id))


@router.post("/majors", summary="创建专业", dependencies=[Depends(require_role("admin", "academic_staff"))])
async def create_major(req: MajorCreate, db: AsyncSession = Depends(get_db)):
    item = await college_service.create_major(db, req)
    return success(data=item)


@router.put("/majors/{major_id}", summary="更新专业", dependencies=[Depends(require_role("admin", "academic_staff"))])
async def update_major(major_id: int, req: MajorUpdate, db: AsyncSession = Depends(get_db)):
    item = await college_service.update_major(db, major_id, req)
    return success(data=item)


@router.delete("/majors/{major_id}", summary="删除专业", dependencies=[Depends(require_role("admin"))])
async def delete_major(major_id: int, db: AsyncSession = Depends(get_db)):
    await college_service.delete_major(db, major_id)
    return success(message="删除成功")


# ========== 学院概览 ==========

@router.get("/college/overview", summary="学院信息概览")
async def get_college_overview(
    college_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取学院概览数据：学工自动使用管辖学院，管理员可指定college_id"""
    # 学工自动使用管辖学院
    if current_user.role_code == 'academic_staff':
        cid = current_user.managed_college_id
    else:
        cid = college_id
    if not cid:
        from app.common.exception import BusinessException
        raise BusinessException(code=400, message="未指定学院ID或没有管辖学院")
    data = await college_service.get_college_overview(db, cid)
    return success(data=data)
