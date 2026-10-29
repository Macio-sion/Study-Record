"""通知公告路由"""
from fastapi import APIRouter, Depends, Query
from app.common.response import success, success_page
from app.common.permission import get_current_user, require_role
from app.dto.notice_schema import NoticeCreate, NoticeUpdate, NoticePageQuery, NoticeRecallCreate, NoticeRecallReview
from app.service import notice_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

notice_router = APIRouter(prefix="/api/notices", tags=["通知公告"])


# ========== 列表与详情（静态路径优先） ==========

@notice_router.get("", summary="分页查询通知列表（按角色过滤）")
async def list_notices(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    is_published: bool = None, target_role: str = None,
    college_id: int = None, major_id: int = None, keyword: str = None,
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),
):
    query = NoticePageQuery(
        page=page, page_size=page_size,
        is_published=is_published, target_role=target_role,
        college_id=college_id, major_id=major_id, keyword=keyword,
    )
    items, total = await notice_service.list_notices(db, query, current_user.id, current_user.role_code)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@notice_router.get("/unviewed/list", summary="获取未查看公告（消息通知用）")
async def get_unviewed(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    items = await notice_service.get_unviewed_notices(db, current_user.id, current_user.role_code)
    return success(data=items)


@notice_router.get("/recall-requests/list", summary="撤回申请列表（管理员）")
async def list_recall_requests(
    status: str = None, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    items = await notice_service.list_recall_requests(db, status)
    return success(data=items)


@notice_router.get("/{notice_id}", summary="查询通知详情（含标记已读）")
async def get_notice(notice_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await notice_service.get_notice(db, notice_id, current_user.id)
    return success(data=result)


# ========== CRUD ==========

@notice_router.post("", summary="创建通知（教师/学工/管理员）")
async def create_notice(
    req: NoticeCreate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff", "teacher")),
):
    result = await notice_service.create_notice(db, current_user.id, current_user.role_code, req)
    return success(data=result)


@notice_router.put("/{notice_id}", summary="更新通知")
async def update_notice(
    notice_id: int, req: NoticeUpdate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff", "teacher")),
):
    result = await notice_service.update_notice(db, notice_id, current_user.id, current_user.role_code, req)
    return success(data=result)


@notice_router.put("/{notice_id}/publish", summary="发布通知")
async def publish_notice(
    notice_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff", "teacher")),
):
    result = await notice_service.publish_notice(db, notice_id, current_user.id, current_user.role_code)
    return success(data=result)


@notice_router.put("/{notice_id}/unpublish", summary="撤回通知")
async def unpublish_notice(
    notice_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff", "teacher")),
):
    result = await notice_service.unpublish_notice(db, notice_id, current_user.id, current_user.role_code)
    return success(data=result)


@notice_router.delete("/{notice_id}", summary="删除通知")
async def delete_notice(
    notice_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff", "teacher")),
):
    await notice_service.delete_notice(db, notice_id, current_user.id, current_user.role_code)
    return success(message="删除成功")


# ========== 撤回申请 ==========

@notice_router.post("/{notice_id}/recall-request", summary="提交撤回申请（超时后）")
async def request_recall(
    notice_id: int, req: NoticeRecallCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher", "academic_staff")),
):
    result = await notice_service.request_recall(db, notice_id, current_user.id, req)
    return success(data=result)


@notice_router.put("/recall-requests/{recall_id}/review", summary="审批撤回申请（管理员）")
async def review_recall(
    recall_id: int, req: NoticeRecallReview,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = await notice_service.review_recall(db, recall_id, current_user.id, req)
    return success(data=result)
