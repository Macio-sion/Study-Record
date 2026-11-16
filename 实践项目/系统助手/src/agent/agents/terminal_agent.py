"""TerminalAgent — 终端命令行操作。"""

from __future__ import annotations

from typing import Any

from agent.base_worker import BaseWorkerAgent
from agent.prompts.terminal_prompt import TERMINAL_AGENT_PROMPT
from utils.constants import ToolCategory


class TerminalAgent(BaseWorkerAgent):
    """终端 Worker，绑定打开终端/修改样式/执行命令等工具。"""

    def __init__(self, provider, config: Any = None) -> None:
        super().__init__(
            provider,
            category=ToolCategory.TERMINAL,
            system_prompt=TERMINAL_AGENT_PROMPT,
            config=config,
        )


__all__ = ["TerminalAgent"]