"""排课管理单元测试"""
import pytest
from app.dto.schedule_schema import ScheduleCreate
from app.service import schedule_service
from app.common.exception import BusinessException


@pytest.mark.asyncio
async def test_create_schedule_success(db_session, seed_data):
    req = ScheduleCreate(
        course_id=seed_data["course_id"], classroom_id=seed_data["classroom_id"],
        teacher_id=seed_data["teacher_id"], semester_id=seed_data["semester_id"],
        week_start=1, week_end=16, day_of_week=1, period_start=1, period_end=3,
    )
    result = await schedule_service.create_schedule(db_session, req)
    assert result.id is not None
    assert result.course_id == seed_data["course_id"]


@pytest.mark.asyncio
async def test_create_schedule_classroom_conflict(db_session, seed_data):
    req1 = ScheduleCreate(
        course_id=seed_data["course_id"], classroom_id=seed_data["classroom_id"],
        teacher_id=seed_data["teacher_id"], semester_id=seed_data["semester_id"],
        week_start=1, week_end=16, day_of_week=1, period_start=1, period_end=3,
    )
    req2 = ScheduleCreate(
        course_id=seed_data["course2_id"], classroom_id=seed_data["classroom_id"],
        teacher_id=seed_data["teacher_id"], semester_id=seed_data["semester_id"],
        week_start=1, week_end=16, day_of_week=1, period_start=2, period_end=4,
    )
    await schedule_service.create_schedule(db_session, req1)
    with pytest.raises(BusinessException, match="已被占用"):
        await schedule_service.create_schedule(db_session, req2)


@pytest.mark.asyncio
async def test_no_conflict_different_rooms(db_session, seed_data):
    req1 = ScheduleCreate(
        course_id=seed_data["course_id"], classroom_id=seed_data["classroom_id"],
        teacher_id=seed_data["teacher_id"], semester_id=seed_data["semester_id"],
        week_start=1, week_end=16, day_of_week=2, period_start=1, period_end=3,
    )
    req2 = ScheduleCreate(
        course_id=seed_data["course2_id"], classroom_id=seed_data["classroom2_id"],
        teacher_id=seed_data["teacher2_id"], semester_id=seed_data["semester_id"],
        week_start=1, week_end=16, day_of_week=2, period_start=1, period_end=3,
    )
    r1 = await schedule_service.create_schedule(db_session, req1)
    r2 = await schedule_service.create_schedule(db_session, req2)
    assert r1.id != r2.id


@pytest.mark.asyncio
async def test_delete_schedule(db_session, seed_data):
    req = ScheduleCreate(
        course_id=seed_data["course_id"], classroom_id=seed_data["classroom_id"],
        teacher_id=seed_data["teacher_id"], semester_id=seed_data["semester_id"],
        week_start=1, week_end=16, day_of_week=3, period_start=1, period_end=3,
    )
    result = await schedule_service.create_schedule(db_session, req)
    assert await schedule_service.delete_schedule(db_session, result.id) is True


@pytest.mark.asyncio
async def test_list_schedules(db_session, seed_data):
    from app.dto.schedule_schema import SchedulePageQuery
    req = ScheduleCreate(
        course_id=seed_data["course_id"], classroom_id=seed_data["classroom_id"],
        teacher_id=seed_data["teacher_id"], semester_id=seed_data["semester_id"],
        week_start=1, week_end=16, day_of_week=4, period_start=1, period_end=3,
    )
    await schedule_service.create_schedule(db_session, req)
    items, total = await schedule_service.list_schedules(db_session, SchedulePageQuery(semester_id=seed_data["semester_id"]))
    assert total >= 1
