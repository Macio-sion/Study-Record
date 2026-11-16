"""Worker Agent 基类。

封装通用的工具调用决策循环：绑定专属工具集，接收用户指令，驱动 LLM 在
「决策 → 调用工具 → 汇总结果」之间迭代，最终产出面向用户的自然语言回复。

每个具体 Worker Agent 只需继承本类并指定：
- ``category``：对应 ``ToolCategory`` 枚举（用于从注册表拉取专属工具）
- ``system_prompt``：该 Agent 的角色与行为规则提示词
"""

from __future__ import annotations

from abc import ABC
from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from loguru import logger

from tools.tool_registry import PermissionDeniedError, ToolRegistry
from utils.constants import ToolCategory
from utils.signal_bus import SignalBus


class BaseWorkerAgent(ABC):
    """Worker Agent 基类（抽象基类）。"""

    category: ToolCategory = ToolCategory.SYSTEM_INFO
    max_iterations: int = 6

    def __init__(
        self,
        provider,
        category: ToolCategory,
        system_prompt: str,
        config: Any = None,
    ) -> None:
        self.provider = provider
        self.category = category
        self.system_prompt = system_prompt
        self.config = config
        self.signal_bus = SignalBus.instance()
        self.tools: List[BaseTool] = ToolRegistry.get_tools_by_category(category)

    # ------------------------------------------------------------------
    def _build_chat_model(self) -> BaseChatModel:
        """构建绑定专属工具的 LLM（每次调用新建，以支持模型热切换）。"""
        llm = self.provider.get_chat_model()
        return llm.bind_tools(self.tools)

    # ------------------------------------------------------------------
    def invoke(self, user_message: str, task_context: Optional[str] = None) -> str:
        """执行一次完整的工具调用决策循环，返回最终自然语言回复。

        Args:
            user_message: 用户原始消息（由 Supervisor 转发）
            task_context: 任务上下文（如任务类型与路由原因）
        """
        messages: List[BaseMessage] = [SystemMessage(content=self.system_prompt)]
        if task_context:
            messages.append(SystemMessage(content=f"任务上下文: {task_context}"))
        messages.append(HumanMessage(content=user_message))

        llm = self._build_chat_model()

        for _ in range(self.max_iterations):
            response = llm.invoke(messages)
            messages.append(response)

            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                return (response.content or "").strip()

            for call in tool_calls:
                name = call.get("name", "")
                args = call.get("args", {}) or {}
                self.signal_bus.tool_executing.emit(name)
                logger.info(f"[{type(self).__name__}] 调用工具: {name}({args})")
                observation = self._execute_tool(name, args)
                messages.append(
                    ToolMessage(content=observation, tool_call_id=call.get("id", ""))
                )

        # 达到最大迭代次数仍未自然结束：取最后一条 assistant 文本
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content.strip()
        return "抱歉，我未能完成该任务，请稍后重试或换个说法。"

    # ------------------------------------------------------------------
    def _execute_tool(self, name: str, args: dict) -> str:
        """执行单个工具并返回其输出文本；异常时返回友好错误供 LLM 汇总。"""
        tool = ToolRegistry.get_tool(name)
        if tool is None:
            return f"错误: 未找到工具 {name}"
        try:
            result = tool.invoke(args)
            return str(result)
        except PermissionDeniedError:
            logger.info(f"工具 {name} 的调用被用户取消")
            return "操作已被用户取消。"
        except Exception as exc:  # noqa: BLE001 - 汇总给 LLM 以生成友好回复
            logger.warning(f"工具 {name} 执行失败: {exc}")
            return f"工具 {name} 执行失败: {exc}"


__all__ = ["BaseWorkerAgent"]