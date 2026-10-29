"""社团管理路由"""
from fastapi import APIRouter, Depends, Query
from app.common.response import success, success_page
from app.common.permission import get_current_user, require_role
from app.dto.club_schema import ClubCreate, ClubUpdate, ClubPageQuery, MemberJoin, MemberApprove
from app.service import club_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

club_router = APIRouter(prefix="/api/clubs", tags=["社团管理"])


# ====== 列表 & 我的 ======

@club_router.get("", summary="分页查询社团列表")
async def list(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    name: str = None,
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),
):
    query = ClubPageQuery(page=page, page_size=page_size, name=name)
    items, total = await club_service.list_clubs(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@club_router.get("/my", summary="我的社团")
async def my_clubs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items = await club_service.list_my_clubs(db, current_user.id)
    return success(data=items)


# ====== CRUD ======

@club_router.post("", summary="创建社团")
async def create(
    req: ClubCreate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff")),
):
    result = await club_service.create_club(db, req)
    return success(data=result)


@club_router.get("/{club_id}", summary="查询社团详情")
async def get(club_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await club_service.get_club(db, club_id)
    return success(data=result)


@club_router.put("/{club_id}", summary="更新社团")
async def update(
    club_id: int, req: ClubUpdate, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff")),
):
    result = await club_service.update_club(db, club_id, req)
    return success(data=result)


@club_router.delete("/{club_id}", summary="删除社团")
async def delete(
    club_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff")),
):
    await club_service.delete_club(db, club_id)
    return success(message="删除成功")


# ====== 成员管理 ======

@club_router.get("/{club_id}/members", summary="社团成员列表")
async def members(
    club_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user),
):
    items, total = await club_service.list_members(db, club_id, page, page_size)
    return success_page(items=items, total=total, page=page, page_size=page_size)


# ====== 加入 / 退出 / 审批 ======

@club_router.post("/members/join", summary="加入社团（管理员直接添加）")
async def join(
    req: MemberJoin, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff")),
):
    result = await club_service.join_club(db, current_user.id, req)
    return success(data=result)


@club_router.post("/members/apply", summary="申请加入社团（学生）")
async def apply(
    req: MemberJoin, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    result = await club_service.apply_club(db, current_user.id, req)
    return success(data=result, message="申请已提交，等待审批")


@club_router.put("/members/{member_id}/approve", summary="审批社团申请")
async def approve(
    member_id: int, req: MemberApprove, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff", "teacher")),
):
    result = await club_service.approve_member(db, member_id, req)
    return success(data=result, message="审批完成")


@club_router.post("/members/leave/{club_id}", summary="退出社团")
async def leave(
    club_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    await club_service.leave_club(db, current_user.id, club_id)
    return success(message="已退出社团")


@club_router.delete("/members/{member_id}", summary="管理员移除成员")
async def remove_member(
    member_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "academic_staff")),
):
    await club_service.remove_member(db, member_id)
    return success(message="成员已移除")
