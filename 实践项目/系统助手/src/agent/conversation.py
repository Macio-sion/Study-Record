"""对话管理器（可拓展记忆）。

提供可插拔的记忆接口 ``BaseMemoryProvider``，默认实现 ``WindowBufferMemory``
（滑动窗口，只保留最近 K 轮对话）。后续可替换为摘要压缩或 SQLite 持久化实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from loguru import logger


class BaseMemoryProvider(ABC):
    """可拓展记忆接口。"""

    @abstractmethod
    def add_message(self, role: str, content: str) -> None:
        """记录一条消息（role 为 user/assistant）。"""

    @abstractmethod
    def get_history(self, k: int = 10) -> List[BaseMessage]:
        """返回最近 k 轮对话历史。"""

    @abstractmethod
    def clear(self) -> None:
        """清空记忆。"""

    @abstractmethod
    def save(self) -> None:
        """持久化当前记忆。"""

    @abstractmethod
    def load(self, session_id: str) -> None:
        """按会话 ID 加载历史记忆。"""


class WindowBufferMemory(BaseMemoryProvider):
    """默认实现：滑动窗口记忆，仅保留最近 ``k`` 轮（每轮 = 用户 + 助手）。"""

    def __init__(self, k: int = 10) -> None:
        self.k = max(1, k)
        self._messages: List[BaseMessage] = []

    def add_message(self, role: str, content: str) -> None:
        if not content:
            return
        if role in ("user", "human"):
            self._messages.append(HumanMessage(content=content))
        else:
            self._messages.append(AIMessage(content=content))

    def get_history(self, k: Optional[int] = None) -> List[BaseMessage]:
        limit = self.k if k is None else k
        return self._messages[-(limit * 2):]

    def clear(self) -> None:
        self._messages.clear()

    def save(self) -> None:
        # 内存实现无需持久化
        return None

    def load(self, session_id: str) -> None:
        # 内存实现不持久化，加载视为空操作
        return None


class ConversationManager:
    """对话管理器 — 使用可插拔记忆策略。"""

    def __init__(self, config: Any = None) -> None:
        self.max_rounds = 10
        if config is not None:
            try:
                self.max_rounds = int(config.tools.max_history_rounds)
            except Exception:  # noqa: BLE001 - 回退默认值
                self.max_rounds = 10
        self.memory_provider: BaseMemoryProvider = self._create_memory_provider()

    # ------------------------------------------------------------------
    def _create_memory_provider(self) -> BaseMemoryProvider:
        """优先使用 Postgres 持久化记忆，不可用时回退内存记忆。"""
        from agent.postgres_memory import PostgresMemoryProvider

        try:
            return PostgresMemoryProvider(k=self.max_rounds)
        except Exception as exc:  # noqa: BLE001 - Postgres 不可用时回退
            logger.warning(f"Postgres 记忆不可用，回退内存记忆: {exc}")
            return WindowBufferMemory(k=self.max_rounds)

    # ------------------------------------------------------------------
    def set_memory_provider(self, provider: BaseMemoryProvider) -> None:
        """运行时切换记忆策略。"""
        self.memory_provider = provider

    def add_user_message(self, content: str) -> None:
        self.memory_provider.add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        self.memory_provider.add_message("assistant", content)

    def get_history(self, k: Optional[int] = None) -> List[BaseMessage]:
        return self.memory_provider.get_history(k or self.max_rounds)

    def clear(self) -> None:
        self.memory_provider.clear()

    def save(self) -> None:
        self.memory_provider.save()

    def load(self, session_id: str) -> None:
        self.memory_provider.load(session_id)


__all__ = [
    "BaseMemoryProvider",
    "WindowBufferMemory",
    "ConversationManager",
]