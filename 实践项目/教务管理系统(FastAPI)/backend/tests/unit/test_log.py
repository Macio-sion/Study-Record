"""操作日志单元测试"""
import pytest
from app.service import log_service
from app.dto.log_schema import LogPageQuery


@pytest.mark.asyncio
async def test_write_log(db_session, seed_data):
    await log_service.write_log(
        db_session, user_id=seed_data["teacher_user_id"],
        action="LOGIN", module="auth", detail="用户登录",
    )
    items, total = await log_service.list_logs(
        db_session, LogPageQuery(user_id=seed_data["teacher_user_id"]),
    )
    assert total >= 1


@pytest.mark.asyncio
async def test_list_logs_filtered(db_session, seed_data):
    await log_service.write_log(db_session, seed_data["teacher_user_id"], "CREATE", "course", detail="创建课程")
    await log_service.write_log(db_session, seed_data["student_user_id"], "UPDATE", "student", detail="更新档案")
    # 按模块筛选
    items, total = await log_service.list_logs(db_session, LogPageQuery(module="course"))
    assert total >= 1
    # 按action筛选
    items2, total2 = await log_service.list_logs(db_session, LogPageQuery(action="UPDATE"))
    assert total2 >= 1


@pytest.mark.asyncio
async def test_empty_logs(db_session):
    items, total = await log_service.list_logs(db_session, LogPageQuery())
    assert total == 0
