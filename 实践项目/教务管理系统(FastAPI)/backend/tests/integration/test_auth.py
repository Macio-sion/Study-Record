"""集成测试：认证模块"""
import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    """登录成功 —— 返回 token + user 信息"""
    resp = await client.post("/api/auth/login", json={
        "username": "admin", "password": "admin123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert "token" in data["data"]
    assert data["data"]["username"] == "admin"
    assert data["data"]["role_code"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """错误密码"""
    resp = await client.post("/api/auth/login", json={
        "username": "admin", "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """不存在的用户"""
    resp = await client.post("/api/auth/login", json={
        "username": "no_such_user_99999", "password": "xxx",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client, admin_token_headers):
    """获取当前登录用户信息"""
    resp = await client.get("/api/users/me", headers=admin_token_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["username"] == "admin"


@pytest.mark.asyncio
async def test_access_without_token(client):
    """无 token 访问受保护接口"""
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_access_with_invalid_token(client):
    """伪造 token"""
    resp = await client.get("/api/users/me", headers={"Authorization": "Bearer fake_token_xxx"})
    assert resp.status_code == 401
