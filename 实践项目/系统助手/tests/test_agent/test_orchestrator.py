"""编排器集成测试 (M-AGT-010 ~ M-AGT-012)。"""

from __future__ import annotations

import asyncio

import pytest

import agent.orchestrator as orchestrator_module
from agent.orchestrator import AgentOrchestrator
from fakes import FakeChatModel
from infrastructure.config.config_manager import ConfigManager
from langchain_core.messages import AIMessage
from utils.constants import TaskType


class _FakeOllamaProvider:
    def __init__(self, config, chat_model=None):
        self.idle_timeout = 30
        self._chat_model = chat_model or FakeChatModel([AIMessage(content="ok")])

    def get_chat_model(self, model_name=None):
        return self._chat_model

    def release_gpu(self):
        return None


@pytest.fixture
def orchestrator(monkeypatch):
    monkeypatch.setattr(orchestrator_module, "OllamaProvider", _FakeOllamaProvider)
    config = ConfigManager().load()
    return AgentOrchestrator(config)


# ---------------------------------------------------------------------------
# 路由映射 (M-AGT-011)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "task_type, expected",
    [
        (TaskType.SYSTEM_INFO.value, TaskType.SYSTEM_INFO.value),
        (TaskType.APP_MANAGER.value, TaskType.APP_MANAGER.value),
        (TaskType.TERMINAL.value, TaskType.TERMINAL.value),
        (TaskType.REGISTRY.value, TaskType.REGISTRY.value),
        (TaskType.ENV_VAR.value, TaskType.ENV_VAR.value),
        (TaskType.KNOWLEDGE_QA.value, TaskType.KNOWLEDGE_QA.value),
        (TaskType.RECYCLE_BIN.value, TaskType.APP_MANAGER.value),  # 回收站绑定 app_manager
        (TaskType.GENERAL_CHAT.value, "GENERAL_CHAT"),
    ],
)
def test_route(task_type, expected):
    assert AgentOrchestrator._route({"task_type": task_type}) == expected


def test_route_unknown_fallback():
    assert AgentOrchestrator._route({"task_type": "UNKNOWN"}) == "GENERAL_CHAT"
    assert AgentOrchestrator._route({}) == "GENERAL_CHAT"


# ---------------------------------------------------------------------------
# 图构建 (M-AGT-010)
# ---------------------------------------------------------------------------
def test_build_graph(orchestrator):
    """M-AGT-010: 构建编译后的状态图。"""
    assert orchestrator.graph is not None
    assert set(orchestrator.workers.keys()) == {
        TaskType.SYSTEM_INFO,
        TaskType.APP_MANAGER,
        TaskType.TERMINAL,
        TaskType.REGISTRY,
        TaskType.ENV_VAR,
        TaskType.KNOWLEDGE_QA,
    }


# ---------------------------------------------------------------------------
# 运行 (M-AGT-012)
# ---------------------------------------------------------------------------
def test_run_general_chat(monkeypatch):
    """阻塞式调用走 GENERAL_CHAT 链路返回回复。"""
    model = FakeChatModel([
        AIMessage(content='{"task_type": "GENERAL_CHAT", "reason": "闲聊"}'),
        AIMessage(content="你好，我是 Windows 系统助手"),
    ])
    monkeypatch.setattr(
        orchestrator_module, "OllamaProvider",
        lambda config: _FakeOllamaProvider(config, chat_model=model),
    )
    orch = AgentOrchestrator(ConfigManager().load())
    result = orch.run("你好")
    assert result == "你好，我是 Windows 系统助手"


def test_astream_emits_status_and_response(monkeypatch):
    """异步流式调用产出 status 与 response 事件。"""
    model = FakeChatModel([
        AIMessage(content='{"task_type": "GENERAL_CHAT", "reason": "闲聊"}'),
        AIMessage(content="你好，我是助手"),
    ])
    monkeypatch.setattr(
        orchestrator_module, "OllamaProvider",
        lambda config: _FakeOllamaProvider(config, chat_model=model),
    )
    orch = AgentOrchestrator(ConfigManager().load())

    async def _collect():
        events = []
        async for event_type, payload in orch.astream("你好"):
            events.append((event_type, payload))
        return events

    events = asyncio.run(_collect())
    types = [e[0] for e in events]
    assert "status" in types
    assert events[-1] == ("response", "你好，我是助手")