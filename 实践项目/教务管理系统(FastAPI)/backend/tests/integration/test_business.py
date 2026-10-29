"""集成测试：核心业务 API (数据用时间戳做唯一键避免冲突)"""
import time
import pytest


@pytest.mark.asyncio
async def test_college_crud_flow(client, admin_token_headers):
    """学院 CRUD: 创建 → 查询 → 列表"""
    ts = hex(int(time.time() * 1000))[-6:]  # 6位短时间戳
    code = f"IT{ts}"
    resp = await client.post("/api/colleges", json={
        "code": code, "name": f"集成测试学院",
    }, headers=admin_token_headers)
    assert resp.status_code == 200
    data = resp.json()
    college_id = data["data"]["id"]

    resp = await client.get(f"/api/colleges/{college_id}", headers=admin_token_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["code"] == code

    resp = await client.get("/api/colleges", headers=admin_token_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_classroom_flow(client, admin_token_headers):
    """教室 CRUD"""
    ts = hex(int(time.time() * 1000))[-4:]
    r = await client.post("/api/classrooms", json={
        "room_no": f"R{ts}", "name": "集成教室", "building": "测试楼", "capacity": 80, "type": "多媒体",
    }, headers=admin_token_headers)
    assert r.status_code == 200
    room_id = r.json()["data"]["id"]

    r = await client.get(f"/api/classrooms/{room_id}", headers=admin_token_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_notice_crud(client, admin_token_headers):
    """通知公告: 创建 → 发布 → 撤回"""
    ts = hex(int(time.time() * 1000))[-4:]
    r = await client.post("/api/notices", json={
        "title": f"集成公告_{ts}", "content": "测试内容", "visible_to": "all",
    }, headers=admin_token_headers)
    assert r.status_code == 200
    notice_id = r.json()["data"]["id"]
    assert not r.json()["data"]["is_published"]

    r = await client.put(f"/api/notices/{notice_id}/publish", headers=admin_token_headers)
    assert r.status_code == 200
    assert r.json()["data"]["is_published"]

    r = await client.put(f"/api/notices/{notice_id}/unpublish", headers=admin_token_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_logs_query(client, admin_token_headers):
    """操作日志查询"""
    r = await client.get("/api/logs", headers=admin_token_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_health_check(client):
    """健康检查"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("healthy", "degraded")
