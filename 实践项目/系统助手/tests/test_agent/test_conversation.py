"""对话管理器单元测试 (M-AGT-014 ~ M-AGT-018)。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from agent.conversation import ConversationManager, WindowBufferMemory
from infrastructure.config.config_manager import ConfigManager


def test_add_message():
    """M-AGT-014: 添加 user + assistant 消息后数量正确。"""
    mem = WindowBufferMemory(k=10)
    mem.add_message("user", "你好")
    mem.add_message("assistant", "你好，有什么可以帮你？")
    history = mem.get_history()
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)


def test_get_history_limit():
    """M-AGT-015: get_history(k=5) 返回最近 5 轮（10 条）。"""
    mem = WindowBufferMemory(k=10)
    for i in range(10):
        mem.add_message("user", f"u{i}")
        mem.add_message("assistant", f"a{i}")
    history = mem.get_history(k=5)
    assert len(history) == 10
    assert history[0].content == "u5"


def test_sliding_window():
    """M-AGT-016: 超过 K 轮自动丢弃最旧消息。"""
    mem = WindowBufferMemory(k=3)
    for i in range(5):
        mem.add_message("user", f"u{i}")
        mem.add_message("assistant", f"a{i}")
    history = mem.get_history()
    assert len(history) == 6
    assert history[0].content == "u2"


def test_clear():
    """M-AGT-017: clear 后消息列表为空。"""
    mem = WindowBufferMemory(k=3)
    mem.add_message("user", "hi")
    mem.clear()
    assert mem.get_history() == []


def test_save_load_noop():
    """M-AGT-018: 内存实现 save/load 为空操作（不抛异常）。"""
    mem = WindowBufferMemory(k=3)
    assert mem.save() is None
    assert mem.load("session_1") is None


def test_conversation_manager_default():
    """补充: ConversationManager 默认最大轮数来自配置，记忆可用。"""
    config = ConfigManager().load()
    cm = ConversationManager(config)
    assert cm.max_rounds == 10

    cm.clear()  # 清空残留，保证测试隔离
    cm.add_user_message("你好")
    cm.add_assistant_message("你好")
    assert len(cm.get_history()) == 2
    cm.clear()