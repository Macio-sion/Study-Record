"""社团管理单元测试"""
import pytest
from app.dto.club_schema import ClubCreate, ClubUpdate, ClubPageQuery, MemberJoin
from app.service import club_service
from app.common.exception import NotFoundException, BusinessException


@pytest.mark.asyncio
async def test_create_club(db_session, seed_data):
    req = ClubCreate(
        name="测试编程社团", description="一起学编程",
        advisor_id=seed_data["teacher_id"],
    )
    result = await club_service.create_club(db_session, req)
    assert result.id is not None
    assert result.name == "测试编程社团"


@pytest.mark.asyncio
async def test_update_club(db_session, seed_data):
    req = ClubCreate(name="原社团名", advisor_id=seed_data["teacher_id"])
    club = await club_service.create_club(db_session, req)
    updated = await club_service.update_club(
        db_session, club.id, ClubUpdate(name="新社团名", description="更新描述"),
    )
    assert updated.name == "新社团名"


@pytest.mark.asyncio
async def test_delete_club(db_session, seed_data):
    req = ClubCreate(name="待删除社团", advisor_id=seed_data["teacher_id"])
    club = await club_service.create_club(db_session, req)
    assert await club_service.delete_club(db_session, club.id) is True
    with pytest.raises(NotFoundException, match="不存在"):
        await club_service.get_club(db_session, club.id)


@pytest.mark.asyncio
async def test_list_clubs(db_session, seed_data):
    req1 = ClubCreate(name="社团A", advisor_id=seed_data["teacher_id"])
    req2 = ClubCreate(name="社团B", advisor_id=seed_data["teacher2_id"])
    await club_service.create_club(db_session, req1)
    await club_service.create_club(db_session, req2)
    items, total = await club_service.list_clubs(db_session, ClubPageQuery())
    assert total >= 2


@pytest.mark.asyncio
async def test_join_leave_club(db_session, seed_data):
    """学生加入和退出社团"""
    club = await club_service.create_club(db_session, ClubCreate(
        name="篮球社", advisor_id=seed_data["teacher_id"],
    ))
    # 加入
    member = await club_service.join_club(db_session, seed_data["student_user_id"], MemberJoin(club_id=club.id))
    assert member.club_id == club.id

    # 重复加入
    with pytest.raises(BusinessException, match="已加入"):
        await club_service.join_club(db_session, seed_data["student_user_id"], MemberJoin(club_id=club.id))

    # 成员列表
    members, total = await club_service.list_members(db_session, club.id)
    assert total >= 1

    # 退出
    assert await club_service.leave_club(db_session, seed_data["student_user_id"], club.id) is True

    # 重复退出
    with pytest.raises(BusinessException, match="未加入"):
        await club_service.leave_club(db_session, seed_data["student_user_id"], club.id)
