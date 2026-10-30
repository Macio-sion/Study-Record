"""PostgreSQL 连接管理。

项目统一约定：后端核心持久化数据（用户/简历/版本/求职记录/反馈/任务日志）落
PostgreSQL；前端任务请求与结果反馈、会话记忆走 Redis（见 services/qa_engine/memory.py
与 queue/）。

这里提供一个轻量的同步连接封装（psycopg2），供 FastAPI 路由（同步 def）与
任务 handler（经 asyncio.to_thread 调用）复用。连接失败时抛出异常，由上层决定是否
回退（例如版本存储已有 InMemoryVersionStore 兜底）。
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
import psycopg2.pool

from config.setting import get_settings

settings = get_settings()

_pool: psycopg2.pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    dbname=settings.postgres_db,
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                )
    return _pool


@contextmanager
def get_conn() -> Iterator[psycopg2.extensions.connection]:
    """获取一个连接（自动提交/回滚/归还）。"""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def ping() -> bool:
    """健康检查：能否连通数据库。"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def init_schema() -> None:
    """按 schema.sql 建表（幂等）。"""
    import os

    sql_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        ddl = f.read()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
