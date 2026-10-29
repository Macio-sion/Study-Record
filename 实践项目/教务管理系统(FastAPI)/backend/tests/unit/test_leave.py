"""请假审批单元测试 — 两级审批流程"""
import pytest
from datetime import date
from app.dto.leave_schema import LeaveCreate, LeaveUpdate
from app.service import leave_service
from app.common.exception import BusinessException, NotFoundException


@pytest.mark.asyncio
async def test_create_leave(db_session, seed_data):
    """学生提交请假申请"""
    req = LeaveCreate(
        course_id=seed_data["course_id"],
        leave_type='事假', leave_date=date.today(),
        reason='家里有事',
    )
    result = await leave_service.create_leave(db_session, seed_data["student_user_id"], req)
    assert result.id is not None
    assert result.status == 'pending_teacher'
    assert result.leave_type == '事假'


@pytest.mark.asyncio
async def test_teacher_approve_reject(db_session, seed_data):
    """教师审批 — 拒绝"""
    req = LeaveCreate(
        course_id=seed_data["course_id"], leave_type='事假',
        leave_date=date.today(), reason='测试',
    )
    leave = await leave_service.create_leave(db_session, seed_data["student_user_id"], req)
    result = await leave_service.approve_teacher(
        db_session, leave.id, seed_data["teacher_user_id"],
        LeaveUpdate(opinion='不同意请假', approved=False),
    )
    assert result.status == 'rejected'
    assert result.teacher_opinion == '不同意请假'


@pytest.mark.asyncio
async def test_two_level_approval(db_session, seed_data):
    """两级审批全流程：学生提交 → 教师通过 → 学工处通过"""
    # 1. 学生提交
    req = LeaveCreate(
        course_id=seed_data["course_id"], leave_type='病假',
        leave_date=date.today(), reason='身体不适',
    )
    leave = await leave_service.create_leave(db_session, seed_data["student_user_id"], req)
    assert leave.status == 'pending_teacher'

    # 2. 教师审批通过
    leave = await leave_service.approve_teacher(
        db_session, leave.id, seed_data["teacher_user_id"],
        LeaveUpdate(opinion='同意', approved=True),
    )
    assert leave.status == 'pending_staff'

    # 3. 学工处审批通过
    leave = await leave_service.approve_staff(
        db_session, leave.id, seed_data["teacher_user_id"],
        LeaveUpdate(opinion='批准', approved=True),
    )
    assert leave.status == 'approved'
    assert leave.staff_opinion == '批准'


@pytest.mark.asyncio
async def test_teacher_approve_wrong_status(db_session, seed_data):
    """已审批的记录不应重复审批"""
    req = LeaveCreate(
        course_id=seed_data["course_id"], leave_type='事假',
        leave_date=date.today(), reason='测试',
    )
    leave = await leave_service.create_leave(db_session, seed_data["student_user_id"], req)
    await leave_service.approve_teacher(
        db_session, leave.id, seed_data["teacher_user_id"],
        LeaveUpdate(opinion='同意', approved=True),
    )
    with pytest.raises(BusinessException, match="不允许教师审批"):
        await leave_service.approve_teacher(
            db_session, leave.id, seed_data["teacher_user_id"],
            LeaveUpdate(opinion='再次审批', approved=True),
        )


@pytest.mark.asyncio
async def test_get_leave_not_found(db_session):
    with pytest.raises(NotFoundException, match="不存在"):
        await leave_service.get_leave(db_session, leave_id=99999)


@pytest.mark.asyncio
async def test_list_leaves(db_session, seed_data):
    req = LeaveCreate(
        course_id=seed_data["course_id"], leave_type='事假',
        leave_date=date.today(), reason='查询测试',
    )
    await leave_service.create_leave(db_session, seed_data["student_user_id"], req)
    from app.dto.leave_schema import LeavePageQuery
    items, total = await leave_service.list_leaves(
        db_session, LeavePageQuery(student_id=seed_data["student_id"]),
    )
    assert total >= 1
