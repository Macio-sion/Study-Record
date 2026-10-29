"""选课管理单元测试"""
import pytest
from app.dto.selection_schema import CourseSelectionCreate
from app.service import selection_service
from app.common.exception import BusinessException, NotFoundException


@pytest.mark.asyncio
async def test_select_course_success(db_session, seed_data):
    req = CourseSelectionCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        semester_id=seed_data["semester_id"],
    )
    result = await selection_service.select_course(db_session, req)
    assert result.id is not None
    assert result.course_id == seed_data["course_id"]
    assert result.status == 'selected'


@pytest.mark.asyncio
async def test_select_course_duplicate(db_session, seed_data):
    req = CourseSelectionCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        semester_id=seed_data["semester_id"],
    )
    await selection_service.select_course(db_session, req)
    with pytest.raises(BusinessException, match="已选择"):
        await selection_service.select_course(db_session, req)


@pytest.mark.asyncio
async def test_drop_course(db_session, seed_data):
    req = CourseSelectionCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        semester_id=seed_data["semester_id"],
    )
    result = await selection_service.select_course(db_session, req)
    assert await selection_service.drop_course(db_session, result.id) is True
    with pytest.raises(BusinessException, match="已退选"):
        await selection_service.drop_course(db_session, result.id)


@pytest.mark.asyncio
async def test_select_course_not_found(db_session, seed_data):
    req = CourseSelectionCreate(course_id=99999, student_id=seed_data["student_id"], semester_id=seed_data["semester_id"])
    with pytest.raises(NotFoundException, match="不存在"):
        await selection_service.select_course(db_session, req)


@pytest.mark.asyncio
async def test_select_course_full(db_session, seed_data):
    from sqlalchemy import update
    from app.model.course import Course
    await db_session.execute(update(Course).where(Course.id == seed_data["course_id"]).values(selected_count=50, max_capacity=50))
    await db_session.flush()
    req = CourseSelectionCreate(
        course_id=seed_data["course_id"], student_id=seed_data["student_id"],
        semester_id=seed_data["semester_id"],
    )
    with pytest.raises(BusinessException, match="容量已满"):
        await selection_service.select_course(db_session, req)
