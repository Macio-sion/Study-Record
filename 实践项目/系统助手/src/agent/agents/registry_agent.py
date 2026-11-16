"""RegistryAgent — 注册表操作。"""

from __future__ import annotations

from typing import Any

from agent.base_worker import BaseWorkerAgent
from agent.prompts.registry_prompt import REGISTRY_AGENT_PROMPT
from utils.constants import ToolCategory


class RegistryAgent(BaseWorkerAgent):
    """注册表 Worker，当前版本绑定打开注册表编辑器工具（高风险）。"""

    def __init__(self, provider, config: Any = None) -> None:
        super().__init__(
            provider,
            category=ToolCategory.REGISTRY,
            system_prompt=REGISTRY_AGENT_PROMPT,
            config=config,
        )


__all__ = ["RegistryAgent"]