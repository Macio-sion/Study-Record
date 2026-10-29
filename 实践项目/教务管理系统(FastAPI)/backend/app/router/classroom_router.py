"""教室管理路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import require_role
from app.dto.classroom_schema import ClassroomCreate, ClassroomUpdate, ClassroomPageQuery
from app.service import classroom_service

classroom_router = APIRouter(prefix="/api/classrooms", tags=["教室管理"])


@classroom_router.get("", summary="教室列表")
async def list_classrooms(page: int = 1, page_size: int = 20, building: str = None, type: str = None, status: str = None, keyword: str = None, db: AsyncSession = Depends(get_db)):
    query = ClassroomPageQuery(page=page, page_size=page_size, building=building, type=type, status=status, keyword=keyword)
    items, total = await classroom_service.list_classrooms(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@classroom_router.get("/{classroom_id}", summary="教室详情")
async def get_classroom(classroom_id: int, db: AsyncSession = Depends(get_db)):
    return success(data=await classroom_service.get_classroom(db, classroom_id))


@classroom_router.post("", summary="创建教室", dependencies=[Depends(require_role("admin"))])
async def create_classroom(req: ClassroomCreate, db: AsyncSession = Depends(get_db)):
    return success(data=await classroom_service.create_classroom(db, req))


@classroom_router.put("/{classroom_id}", summary="更新教室", dependencies=[Depends(require_role("admin"))])
async def update_classroom(classroom_id: int, req: ClassroomUpdate, db: AsyncSession = Depends(get_db)):
    return success(data=await classroom_service.update_classroom(db, classroom_id, req))


@classroom_router.delete("/{classroom_id}", summary="删除教室", dependencies=[Depends(require_role("admin"))])
async def delete_classroom(classroom_id: int, db: AsyncSession = Depends(get_db)):
    await classroom_service.delete_classroom(db, classroom_id)
    return success(message="删除成功")
