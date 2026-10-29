"""成绩管理单元测试"""
import pytest
from decimal import Decimal
from app.dto.score_schema import ScoreCreate, ScoreUpdate, ScorePageQuery
from app.service import score_service
from app.common.exception import NotFoundException


@pytest.mark.asyncio
async def test_create_score(db_session, seed_data):
    req = ScoreCreate(
        student_id=seed_data["student_id"], course_id=seed_data["course_id"],
        semester_id=seed_data["semester_id"], teacher_id=seed_data["teacher_id"],
        score=Decimal("85.5"),
    )
    result = await score_service.create_score(db_session, operator_id=seed_data["teacher_user_id"], req=req)
    assert result.id is not None
    assert result.score == Decimal("85.5")
    assert result.student_id == seed_data["student_id"]


@pytest.mark.asyncio
async def test_update_score(db_session, seed_data):
    req = ScoreCreate(
        student_id=seed_data["student_id"], course_id=seed_data["course_id"],
        semester_id=seed_data["semester_id"], teacher_id=seed_data["teacher_id"],
        score=Decimal("70.0"),
    )
    result = await score_service.create_score(db_session, operator_id=seed_data["teacher_user_id"], req=req)
    updated = await score_service.update_score(
        db_session, operator_id=seed_data["teacher_user_id"],
        score_id=result.id, req=ScoreUpdate(score=Decimal("90.0")),
    )
    assert updated.score == Decimal("90.0")


@pytest.mark.asyncio
async def test_get_score(db_session, seed_data):
    req = ScoreCreate(
        student_id=seed_data["student_id"], course_id=seed_data["course_id"],
        semester_id=seed_data["semester_id"], teacher_id=seed_data["teacher_id"],
        score=Decimal("88.0"),
    )
    result = await score_service.create_score(db_session, operator_id=seed_data["teacher_user_id"], req=req)
    fetched = await score_service.get_score(db_session, score_id=result.id)
    assert fetched.id == result.id
    assert fetched.score == Decimal("88.0")


@pytest.mark.asyncio
async def test_list_scores(db_session, seed_data):
    req1 = ScoreCreate(
        student_id=seed_data["student_id"], course_id=seed_data["course_id"],
        semester_id=seed_data["semester_id"], teacher_id=seed_data["teacher_id"],
        score=Decimal("82.0"),
    )
    req2 = ScoreCreate(
        student_id=seed_data["student2_id"], course_id=seed_data["course_id"],
        semester_id=seed_data["semester_id"], teacher_id=seed_data["teacher_id"],
        score=Decimal("95.0"),
    )
    await score_service.create_score(db_session, operator_id=seed_data["teacher_user_id"], req=req1)
    await score_service.create_score(db_session, operator_id=seed_data["teacher_user_id"], req=req2)
    items, total = await score_service.list_scores(db_session, ScorePageQuery(course_id=seed_data["course_id"]))
    assert total >= 2


@pytest.mark.asyncio
async def test_get_score_not_found(db_session):
    with pytest.raises(NotFoundException, match="不存在"):
        await score_service.get_score(db_session, score_id=99999)
