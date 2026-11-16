"""Postgres 持久化记忆 Provider。

将会话记忆（用户/助手消息）持久化到 Postgres 的 ``chat_memory`` 表，
实现 ``BaseMemoryProvider`` 接口，供 ``ConversationManager`` 插拔使用。
"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from loguru import logger

from agent.conversation import BaseMemoryProvider
from infrastructure.postgres.pg_config import PostgresConfig

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_memory (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
"""

_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_chat_memory_session "
    "ON chat_memory (session_id, id);"
)


class PostgresMemoryProvider(BaseMemoryProvider):
    """基于 Postgres 的会话记忆持久化。"""

    def __init__(
        self,
        session_id: str = "default",
        k: int = 10,
        pg_config: Optional[PostgresConfig] = None,
    ) -> None:
        self.k = max(1, k)
        self.session_id = session_id
        self.pg_config = pg_config or PostgresConfig().load()
        self._ensure_table()

    # ------------------------------------------------------------------
    def _connect(self):
        import psycopg

        return psycopg.connect(
            host=self.pg_config.host,
            port=self.pg_config.port,
            user=self.pg_config.user,
            password=self.pg_config.password,
            dbname=self.pg_config.database,
            connect_timeout=5,
        )

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute(_TABLE_SQL)
            conn.execute(_INDEX_SQL)
            conn.commit()

    # ------------------------------------------------------------------
    def add_message(self, role: str, content: str) -> None:
        """持久化一条消息。"""
        if not content:
            return
        normalized = "user" if role in ("user", "human") else "assistant"
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO chat_memory (session_id, role, content) "
                    "VALUES (%s, %s, %s);",
                    (self.session_id, normalized, content),
                )
                conn.commit()
        except Exception as exc:  # noqa: BLE001 - 持久化失败不影响主流程
            logger.warning(f"持久化记忆失败: {exc}")

    def get_history(self, k: Optional[int] = None) -> List[BaseMessage]:
        """返回当前会话最近 k 轮对话（每轮 = 用户 + 助手）。"""
        limit = self.k if k is None else k
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT role, content FROM chat_memory "
                    "WHERE session_id = %s ORDER BY id DESC LIMIT %s;",
                    (self.session_id, limit * 2),
                ).fetchall()
        except Exception as exc:  # noqa: BLE001 - 读取失败返回空
            logger.warning(f"读取记忆失败: {exc}")
            return []

        messages: List[BaseMessage] = []
        for role, content in reversed(rows):
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        return messages

    def clear(self) -> None:
        """清空当前会话的记忆。"""
        try:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM chat_memory WHERE session_id = %s;",
                    (self.session_id,),
                )
                conn.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"清空记忆失败: {exc}")

    def save(self) -> None:
        """已实时持久化，无需额外保存。"""
        return None

    def load(self, session_id: str) -> None:
        """切换到指定会话 ID。"""
        self.session_id = session_id


__all__ = ["PostgresMemoryProvider"]
