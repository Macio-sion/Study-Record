"""上传文件在 Redis 中的暂存（网络字节流 → Redis，带 TTL）。

文件解析任务解耦为两步：前端先上传字节流换取 ``file_id``，再提交任务；
worker 侧按 ``file_id`` 取回字节流交给解析引擎，避免把大体积二进制塞进 Docket 队列。
"""

from __future__ import annotations

import uuid

import redis

from config.setting import get_settings

settings = get_settings()

_FILE_PREFIX = "resume:file:"


def _client() -> redis.Redis:
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=False,  # 字节流需要原始二进制
        socket_connect_timeout=2,
    )


def store_file(data: bytes) -> str:
    """暂存文件字节流，返回 file_id。"""
    file_id = f"f{uuid.uuid4().hex}"
    client = _client()
    client.set(f"{_FILE_PREFIX}{file_id}", data, ex=settings.file_ttl_seconds)
    return file_id


def load_file(file_id: str) -> bytes | None:
    """按 file_id 取回字节流，不存在或已过期返回 None。"""
    client = _client()
    return client.get(f"{_FILE_PREFIX}{file_id}")
