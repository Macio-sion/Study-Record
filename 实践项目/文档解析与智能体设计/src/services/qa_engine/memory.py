"""节点（记忆持久化）业务代码：会话记忆存储（Redis + 内存兜底）+ 敏感信息脱敏"""

import json
import re
import uuid
from abc import ABC, abstractmethod
from typing import List

import redis

from config.setting import get_settings

settings = get_settings()

# 脱敏正则：手机号 138****5678、邮箱 a***@xx.com
PHONE_RE = re.compile(r"(1[3-9]\d)\d{4}(\d{4})")
EMAIL_RE = re.compile(r"([a-zA-Z0-9])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")


class MemoryStore(ABC):
    """会话记忆存储接口（get/append/clear），可切换 Redis / 内存 / PostgreSQL 等实现"""

    @abstractmethod
    def get(self, session_id: str) -> List[dict]:
        """读取会话历史，不存在返回空列表"""

    @abstractmethod
    def append(self, session_id: str, turn: dict) -> List[dict]:
        """追加一轮对话，返回更新后的历史"""

    @abstractmethod
    def clear(self, session_id: str) -> None:
        """清空会话记忆"""


class InMemoryMemoryStore(MemoryStore):
    """内存存储：进程内 dict，用于开发/测试兜底"""

    def __init__(self) -> None:
        self._sessions: dict = {}

    def get(self, session_id: str) -> List[dict]:
        return self._sessions.get(session_id, [])

    def append(self, session_id: str, turn: dict) -> List[dict]:
        history = self._sessions.setdefault(session_id, [])
        history.append(turn)
        return history

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


class RedisMemoryStore(MemoryStore):
    """Redis 存储：会话历史以 JSON 存于 key=qa:session:{session_id}"""

    def __init__(self, host: str = None, port: int = None, db: int = None, key_prefix: str = "qa:session:"):
        self.key_prefix = key_prefix
        self.client = redis.Redis(
            host=host or settings.redis_host,
            port=port or settings.redis_port,
            db=db if db is not None else settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=2,
        )

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"

    def get(self, session_id: str) -> List[dict]:
        raw = self.client.get(self._key(session_id))
        if raw is None:
            return []
        return json.loads(raw)

    def append(self, session_id: str, turn: dict) -> List[dict]:
        history = self.get(session_id)
        history.append(turn)
        self.client.set(self._key(session_id), json.dumps(history, ensure_ascii=False))
        return history

    def clear(self, session_id: str) -> None:
        self.client.delete(self._key(session_id))


def desensitize(text: str) -> str:
    """对手机号/邮箱脱敏（138****5678、a***@xx.com）"""
    text = PHONE_RE.sub(r"\1****\2", text)
    text = EMAIL_RE.sub(r"\1***\2", text)
    return text


def new_session_id() -> str:
    """生成会话 ID"""
    return f"sess_{uuid.uuid4().hex[:8]}"


def create_memory_store() -> MemoryStore:
    """优先 Redis，连接失败回退内存存储"""
    try:
        store = RedisMemoryStore()
        store.client.ping()
        return store
    except Exception:
        return InMemoryMemoryStore()


# 模块级默认存储（共享运行时）
memory_store = create_memory_store()
