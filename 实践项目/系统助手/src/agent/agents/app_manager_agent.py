"""AppManagerAgent — 应用管理与回收站管理。"""

from __future__ import annotations

from typing import Any

from agent.base_worker import BaseWorkerAgent
from agent.prompts.app_manager_prompt import APP_MANAGER_AGENT_PROMPT
from utils.constants import ToolCategory


class AppManagerAgent(BaseWorkerAgent):
    """应用管理 Worker，绑定应用列表/详情/启动/关闭及回收站工具。"""

    def __init__(self, provider, config: Any = None) -> None:
        super().__init__(
            provider,
            category=ToolCategory.APP_MANAGER,
            system_prompt=APP_MANAGER_AGENT_PROMPT,
            config=config,
        )


__all__ = ["AppManagerAgent"]