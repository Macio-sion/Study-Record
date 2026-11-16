"""Supervisor 路由代理。

负责意图识别与任务路由：将用户自然语言分类到 ``TaskType`` 枚举之一，
并附带分类理由。Supervisor 不绑定任何工具，仅做纯分类决策。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger

from agent.prompts.supervisor_prompt import SUPERVISOR_PROMPT
from utils.constants import TaskType


@dataclass
class SupervisorResult:
    """Supervisor 分类结果。"""

    task_type: TaskType
    reason: str


class SupervisorAgent:
    """意图识别与路由代理。"""

    def __init__(self, provider, config: Any = None) -> None:
        self.provider = provider
        self.config = config

    # ------------------------------------------------------------------
    def classify(
        self,
        user_message: str,
        history: Optional[List[BaseMessage]] = None,
    ) -> SupervisorResult:
        """识别用户意图，返回任务分类结果。"""
        messages: List[BaseMessage] = [SystemMessage(content=SUPERVISOR_PROMPT)]
        if history:
            messages.extend(history)
        messages.append(HumanMessage(content=user_message))

        llm = self.provider.get_chat_model()
        response = llm.invoke(messages)
        content = response.content or ""
        data = self._parse_json(content)
        task_type = self._coerce_task_type(data.get("task_type"))
        reason = str(data.get("reason", ""))
        logger.info(f"Supervisor 分类结果: {task_type.value} ({reason})")
        return SupervisorResult(task_type=task_type, reason=reason)

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_json(content: str) -> dict:
        """解析模型输出为 dict，容忍非纯 JSON 输出。"""
        if not content:
            return {}
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass
        # 兜底：提取首个 JSON 对象片段
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except (json.JSONDecodeError, ValueError):
                pass
        return {}

    @staticmethod
    def _coerce_task_type(value: Any) -> TaskType:
        """将任意值规整为 TaskType，非法值回退为 GENERAL_CHAT。"""
        if isinstance(value, TaskType):
            return value
        try:
            return TaskType(str(value).strip().upper())
        except (ValueError, AttributeError):
            return TaskType.GENERAL_CHAT


__all__ = ["SupervisorAgent", "SupervisorResult"]