"""EnvVarAgent — 环境变量管理。"""

from __future__ import annotations

from typing import Any

from agent.base_worker import BaseWorkerAgent
from agent.prompts.env_var_prompt import ENV_VAR_AGENT_PROMPT
from utils.constants import ToolCategory


class EnvVarAgent(BaseWorkerAgent):
    """环境变量 Worker，绑定查看/修改环境变量工具。"""

    def __init__(self, provider, config: Any = None) -> None:
        super().__init__(
            provider,
            category=ToolCategory.ENV_VAR,
            system_prompt=ENV_VAR_AGENT_PROMPT,
            config=config,
        )


__all__ = ["EnvVarAgent"]