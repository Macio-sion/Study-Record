"""考勤管理单元测试"""
import pytest
from datetime import date
from app.dto.attendance_schema import AttendanceCreate
from app.service import attendance_service


@pytest.mark.asyncio
async def test_create_attendance(db_session, seed_data):
    req = AttendanceCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        teacher_id=seed_data["teacher_id"], date=date.today(), status='present',
    )
    result = await attendance_service.create_attendance(db_session, req)
    assert result.id is not None
    assert result.status == 'present'


@pytest.mark.asyncio
async def test_batch_attendance(db_session, seed_data):
    records = [
        AttendanceCreate(
            course_id=seed_data["course_id"], student_id=seed_data["student_id"],
            teacher_id=seed_data["teacher_id"], date=date.today(), status='present',
        ),
        AttendanceCreate(
            course_id=seed_data["course_id"], student_id=seed_data["student2_id"],
            teacher_id=seed_data["teacher_id"], date=date.today(), status='absent', remark='未到',
        ),
    ]
    results = await attendance_service.batch_create_attendance(db_session, records)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_get_attendance_stats(db_session, seed_data):
    req1 = AttendanceCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        teacher_id=seed_data["teacher_id"], date=date.today(), status='present',
    )
    req2 = AttendanceCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        teacher_id=seed_data["teacher_id"], date=date(2026, 7, 21), status='absent',
    )
    await attendance_service.create_attendance(db_session, req1)
    await attendance_service.create_attendance(db_session, req2)
    stats = await attendance_service.get_attendance_stats(db_session, student_id=seed_data["student_id"])
    assert stats.total == 2
    assert stats.present == 1
    assert stats.absent == 1
    assert stats.rate == 0.5


@pytest.mark.asyncio
async def test_update_attendance(db_session, seed_data):
    req = AttendanceCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        teacher_id=seed_data["teacher_id"], date=date.today(), status='absent',
    )
    result = await attendance_service.create_attendance(db_session, req)
    from app.dto.attendance_schema import AttendanceUpdate
    updated = await attendance_service.update_attendance(db_session, result.id, AttendanceUpdate(status='late', remark='补签到'))
    assert updated.status == 'late'
