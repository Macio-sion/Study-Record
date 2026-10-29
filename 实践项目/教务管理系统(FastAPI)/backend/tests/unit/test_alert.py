"""学业预警单元测试"""
import pytest
from decimal import Decimal
from app.dto.alert_schema import AlertCreate, AlertHandle
from app.service import alert_service
from app.common.exception import NotFoundException


@pytest.mark.asyncio
async def test_create_alert(db_session, seed_data):
    req = AlertCreate(
        student_id=seed_data["student_id"], semester_id=seed_data["semester_id"],
        alert_level='warning', attendance_rate=Decimal("0.65"), failed_count=2,
    )
    result = await alert_service.create_alert(db_session, req)
    assert result.id is not None
    assert result.alert_level == 'warning'
    assert result.status == 'pending'


@pytest.mark.asyncio
async def test_handle_alert(db_session, seed_data):
    req = AlertCreate(
        student_id=seed_data["student_id"], semester_id=seed_data["semester_id"],
        alert_level='serious', failed_count=3,
    )
    alert = await alert_service.create_alert(db_session, req)
    result = await alert_service.handle_alert(
        db_session, alert.id, seed_data["teacher_user_id"],
        AlertHandle(handle_result="已约谈学生家长"),
    )
    assert result.status == 'handled'
    assert result.handle_result == "已约谈学生家长"


@pytest.mark.asyncio
async def test_get_alert(db_session, seed_data):
    req = AlertCreate(
        student_id=seed_data["student_id"], semester_id=seed_data["semester_id"],
        alert_level='critical', failed_count=5,
    )
    alert = await alert_service.create_alert(db_session, req)
    fetched = await alert_service.get_alert(db_session, alert.id)
    assert fetched.id == alert.id


@pytest.mark.asyncio
async def test_get_alert_not_found(db_session):
    with pytest.raises(NotFoundException, match="不存在"):
        await alert_service.get_alert(db_session, alert_id=99999)


@pytest.mark.asyncio
async def test_list_alerts(db_session, seed_data):
    req = AlertCreate(
        student_id=seed_data["student_id"], semester_id=seed_data["semester_id"],
        alert_level='warning', failed_count=1,
    )
    await alert_service.create_alert(db_session, req)
    from app.dto.alert_schema import AlertPageQuery
    items, total = await alert_service.list_alerts(
        db_session, AlertPageQuery(student_id=seed_data["student_id"]),
    )
    assert total >= 1
