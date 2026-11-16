"""Worker Agent 基类单元测试 (M-AGT-013)。"""

from __future__ import annotations

import tools  # noqa: F401 - 触发工具注册

from langchain_core.messages import AIMessage

from agent.base_worker import BaseWorkerAgent
from fakes import FakeChatModel, FakeProvider
from utils.constants import ToolCategory


def test_init_binds_tools():
    """M-AGT-013: 构造时绑定专属工具集非空。"""
    worker = BaseWorkerAgent(FakeProvider(), ToolCategory.SYSTEM_INFO, "系统信息助手")
    assert len(worker.tools) == 5


def test_build_chat_model_binds_tools():
    """补充: _build_chat_model 调用 bind_tools 并绑定工具。"""
    fake = FakeChatModel([AIMessage(content="ok")])
    worker = BaseWorkerAgent(FakeProvider(fake), ToolCategory.SYSTEM_INFO, "p")
    llm = worker._build_chat_model()
    assert llm.bound_tools == worker.tools


def test_invoke_no_tool_call_returns_content():
    """补充: 无工具调用时直接返回模型文本。"""
    fake = FakeChatModel([AIMessage(content="磁盘信息如下")])
    worker = BaseWorkerAgent(FakeProvider(fake), ToolCategory.SYSTEM_INFO, "p")
    assert worker.invoke("查看磁盘") == "磁盘信息如下"


def test_invoke_with_tool_call_executes_tool():
    """补充: 带工具调用时执行工具并返回最终回复。"""
    fake = FakeChatModel([
        AIMessage(content="", tool_calls=[{
            "name": "get_disk_info", "args": {}, "id": "call_1", "type": "tool_call",
        }]),
        AIMessage(content="已获取磁盘信息"),
    ])
    worker = BaseWorkerAgent(FakeProvider(fake), ToolCategory.SYSTEM_INFO, "p")
    assert worker.invoke("查看磁盘") == "已获取磁盘信息"


def test_execute_tool_not_found():
    """补充: 调用不存在的工具返回错误提示。"""
    worker = BaseWorkerAgent(FakeProvider(), ToolCategory.SYSTEM_INFO, "p")
    result = worker._execute_tool("__no_such_tool__", {})
    assert "未找到工具" in result