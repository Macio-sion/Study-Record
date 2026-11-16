"""Supervisor 意图识别单元测试 (M-AGT-001 ~ M-AGT-009)。"""

from __future__ import annotations

import pytest

from langchain_core.messages import AIMessage

from agent.supervisor import SupervisorAgent, SupervisorResult
from fakes import FakeChatModel, FakeProvider
from utils.constants import TaskType


def _classify(raw_content: str) -> SupervisorResult:
    model = FakeChatModel([AIMessage(content=raw_content)])
    provider = FakeProvider(model)
    return SupervisorAgent(provider).classify("测试输入")


def _json(task_type: str, reason: str = "测试") -> str:
    return '{"task_type": "%s", "reason": "%s"}' % (task_type, reason)


@pytest.mark.parametrize(
    "raw, expected",
    [
        (_json("SYSTEM_INFO"), TaskType.SYSTEM_INFO),
        (_json("APP_MANAGER"), TaskType.APP_MANAGER),
        (_json("TERMINAL"), TaskType.TERMINAL),
        (_json("REGISTRY"), TaskType.REGISTRY),
        (_json("ENV_VAR"), TaskType.ENV_VAR),
        (_json("RECYCLE_BIN"), TaskType.RECYCLE_BIN),
        (_json("GENERAL_CHAT"), TaskType.GENERAL_CHAT),
    ],
)
def test_classify_task_types(raw, expected):
    """M-AGT-001~007: 各类意图均正确识别。"""
    result = _classify(raw)
    assert result.task_type == expected


def test_classify_invalid_type_fallback():
    """M-AGT-008: 无法解析的任务类型回退到 GENERAL_CHAT。"""
    result = _classify(_json("BOGUS"))
    assert result.task_type == TaskType.GENERAL_CHAT


def test_classify_invalid_json_fallback():
    """M-AGT-009: LLM 返回格式错误时回退 GENERAL_CHAT。"""
    result = _classify("这不是 JSON 格式的输出")
    assert result.task_type == TaskType.GENERAL_CHAT


def test_classify_json_with_surrounding_text():
    """补充: 从夹杂文本中提取 JSON 对象。"""
    result = _classify('好的，结果是：{"task_type": "ENV_VAR", "reason": "设置变量"}')
    assert result.task_type == TaskType.ENV_VAR


def test_parse_json_plain():
    assert SupervisorAgent._parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_empty():
    assert SupervisorAgent._parse_json("") == {}
    assert SupervisorAgent._parse_json("no json here") == {}


def test_coerce_task_type():
    assert SupervisorAgent._coerce_task_type("system_info") == TaskType.SYSTEM_INFO
    assert SupervisorAgent._coerce_task_type("INVALID") == TaskType.GENERAL_CHAT
    assert SupervisorAgent._coerce_task_type(TaskType.REGISTRY) == TaskType.REGISTRY
    assert SupervisorAgent._coerce_task_type(None) == TaskType.GENERAL_CHAT