"""集成测试共享 fixtures —— 使用 ASGI Transport 直接测试 FastAPI 应用"""
import os
import sys

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.main import app
from app.config import settings
from app.model.base import Base
from app.model import *  # noqa
from app.common.security import hash_password


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(test_engine):
    """创建 ASGI 客户端 —— 使用测试引擎替换模块引擎"""
    import app.database as db_mod
    original = db_mod.engine
    db_mod.engine = test_engine
    # 重建 sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    db_mod.AsyncSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    db_mod.engine = original
    db_mod.AsyncSessionLocal = async_sessionmaker(original, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def admin_token_headers(client):
    """获取 admin 用户的 token 和 headers"""
    resp = await client.post("/api/auth/login", json={
        "username": "admin", "password": "admin123",
    })
    data = resp.json()
    token = data["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
