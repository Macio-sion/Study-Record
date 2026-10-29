"""学业预警路由"""
from fastapi import APIRouter, Depends, Query
from app.common.response import success, success_page
from app.common.permission import get_current_user, require_role
from app.dto.alert_schema import AlertCreate, AlertHandle, AlertPageQuery
from app.service import alert_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

alert_router = APIRouter(prefix="/api/alerts", tags=["学业预警"])


@alert_router.post("", summary="创建学业预警")
async def create(
    req: AlertCreate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff")),
):
    result = await alert_service.create_alert(db, req)
    return success(data=result)


@alert_router.put("/{alert_id}/handle", summary="处理预警")
async def handle(
    alert_id: int, req: AlertHandle, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff")),
):
    result = await alert_service.handle_alert(db, alert_id, current_user.id, req)
    return success(data=result)


@alert_router.get("/{alert_id}", summary="查询预警详情")
async def get(alert_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await alert_service.get_alert(db, alert_id)
    return success(data=result)


@alert_router.get("", summary="分页查询预警列表")
async def list(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    student_id: int = None, semester_id: int = None,
    alert_level: str = None, status: str = None, keyword: str = None,
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),
):
    query = AlertPageQuery(page=page, page_size=page_size, student_id=student_id, semester_id=semester_id, alert_level=alert_level, status=status, keyword=keyword)
    college_id = current_user.managed_college_id if current_user.role_code == 'academic_staff' else None
    items, total = await alert_service.list_alerts(db, query, college_id=college_id)
    return success_page(items=items, total=total, page=page, page_size=page_size)
