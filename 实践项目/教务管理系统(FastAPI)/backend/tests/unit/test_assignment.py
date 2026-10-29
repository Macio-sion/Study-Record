"""作业管理单元测试"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.dto.assignment_schema import (
    AssignmentCreate, AssignmentUpdate, AssignmentPageQuery,
    SubmissionCreate, SubmissionReview,
)
from app.service import assignment_service
from app.common.exception import NotFoundException


@pytest.mark.asyncio
async def test_create_assignment(db_session, seed_data):
    deadline = datetime.now() + timedelta(days=7)
    req = AssignmentCreate(
        course_id=seed_data["course_id"], teacher_id=seed_data["teacher_id"],
        title="第一次课后作业", content="请完成第1-3章习题", deadline=deadline,
    )
    result = await assignment_service.create_assignment(db_session, req)
    assert result.id is not None
    assert result.title == "第一次课后作业"
    assert result.course_id == seed_data["course_id"]


@pytest.mark.asyncio
async def test_update_assignment(db_session, seed_data):
    deadline = datetime.now() + timedelta(days=7)
    req = AssignmentCreate(
        course_id=seed_data["course_id"], teacher_id=seed_data["teacher_id"],
        title="原作业标题", content="原内容", deadline=deadline,
    )
    result = await assignment_service.create_assignment(db_session, req)
    new_deadline = datetime.now() + timedelta(days=14)
    updated = await assignment_service.update_assignment(
        db_session, assignment_id=result.id,
        req=AssignmentUpdate(title="更新后作业标题", deadline=new_deadline),
    )
    assert updated.title == "更新后作业标题"


@pytest.mark.asyncio
async def test_delete_assignment(db_session, seed_data):
    deadline = datetime.now() + timedelta(days=3)
    req = AssignmentCreate(
        course_id=seed_data["course_id"], teacher_id=seed_data["teacher_id"],
        title="可删除作业", deadline=deadline,
    )
    result = await assignment_service.create_assignment(db_session, req)
    assert await assignment_service.delete_assignment(db_session, result.id) is True
    with pytest.raises(NotFoundException, match="不存在"):
        await assignment_service.get_assignment(db_session, result.id)


@pytest.mark.asyncio
async def test_list_assignments(db_session, seed_data):
    deadline = datetime.now() + timedelta(days=5)
    req1 = AssignmentCreate(
        course_id=seed_data["course_id"], teacher_id=seed_data["teacher_id"],
        title="作业1", deadline=deadline,
    )
    req2 = AssignmentCreate(
        course_id=seed_data["course_id"], teacher_id=seed_data["teacher_id"],
        title="作业2", deadline=deadline + timedelta(hours=1),
    )
    await assignment_service.create_assignment(db_session, req1)
    await assignment_service.create_assignment(db_session, req2)
    items, total = await assignment_service.list_assignments(
        db_session, AssignmentPageQuery(course_id=seed_data["course_id"]),
    )
    assert total >= 2


@pytest.mark.asyncio
async def test_get_assignment_not_found(db_session):
    with pytest.raises(NotFoundException, match="不存在"):
        await assignment_service.get_assignment(db_session, assignment_id=99999)


@pytest.mark.asyncio
async def test_submit_and_review(db_session, seed_data):
    deadline = datetime.now() + timedelta(days=7)
    ass = await assignment_service.create_assignment(db_session, AssignmentCreate(
        course_id=seed_data["course_id"], teacher_id=seed_data["teacher_id"],
        title="提交测试作业", deadline=deadline,
    ))
    sub = await assignment_service.submit_assignment(db_session, SubmissionCreate(
        assignment_id=ass.id, student_id=seed_data["student_id"], content="这是我的作业提交内容",
    ))
    assert sub.id is not None
    assert sub.content == "这是我的作业提交内容"

    reviewed = await assignment_service.review_submission(db_session, sub.id, SubmissionReview(
        score=Decimal("92"), comment="完成度很高",
    ))
    assert reviewed.score == Decimal("92")
    assert reviewed.comment == "完成度很高"
