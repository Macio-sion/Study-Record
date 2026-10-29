"""通知公告单元测试"""
import pytest
from app.dto.notice_schema import NoticeCreate, NoticeUpdate, NoticePageQuery
from app.service import notice_service
from app.common.exception import NotFoundException


@pytest.mark.asyncio
async def test_create_notice(db_session, seed_data):
    req = NoticeCreate(title="放假通知", content="下周放假三天", visible_to="all")
    result = await notice_service.create_notice(db_session, publisher_id=seed_data["teacher_user_id"], req=req)
    assert result.id is not None
    assert result.title == "放假通知"
    assert not result.is_published


@pytest.mark.asyncio
async def test_publish_notice(db_session, seed_data):
    req = NoticeCreate(title="考试通知", content="下周一考试", visible_to="student")
    notice = await notice_service.create_notice(db_session, publisher_id=seed_data["teacher_user_id"], req=req)
    result = await notice_service.publish_notice(db_session, notice.id)
    assert result.is_published
    assert result.published_at is not None


@pytest.mark.asyncio
async def test_unpublish_notice(db_session, seed_data):
    req = NoticeCreate(title="测试通知", content="test", visible_to="all")
    notice = await notice_service.create_notice(db_session, publisher_id=seed_data["teacher_user_id"], req=req)
    await notice_service.publish_notice(db_session, notice.id)
    result = await notice_service.unpublish_notice(db_session, notice.id)
    assert not result.is_published
    assert result.published_at is None


@pytest.mark.asyncio
async def test_delete_notice(db_session, seed_data):
    req = NoticeCreate(title="待删除", visible_to="all")
    notice = await notice_service.create_notice(db_session, publisher_id=seed_data["teacher_user_id"], req=req)
    assert await notice_service.delete_notice(db_session, notice.id) is True
    with pytest.raises(NotFoundException, match="不存在"):
        await notice_service.get_notice(db_session, notice.id)


@pytest.mark.asyncio
async def test_list_notices(db_session, seed_data):
    req1 = NoticeCreate(title="通知1", visible_to="all")
    req2 = NoticeCreate(title="通知2", visible_to="teacher")
    await notice_service.create_notice(db_session, publisher_id=seed_data["teacher_user_id"], req=req1)
    await notice_service.create_notice(db_session, publisher_id=seed_data["teacher_user_id"], req=req2)
    items, total = await notice_service.list_notices(db_session, NoticePageQuery())
    assert total >= 2
