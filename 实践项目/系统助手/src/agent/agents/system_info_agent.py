"""SystemInfoAgent — 系统信息查看。"""

from __future__ import annotations

from typing import Any

from agent.base_worker import BaseWorkerAgent
from agent.prompts.system_info_prompt import SYSTEM_INFO_AGENT_PROMPT
from utils.constants import ToolCategory


class SystemInfoAgent(BaseWorkerAgent):
    """系统信息 Worker，绑定磁盘/网络/内存/进程/设备等只读工具。"""

    def __init__(self, provider, config: Any = None) -> None:
        super().__init__(
            provider,
            category=ToolCategory.SYSTEM_INFO,
            system_prompt=SYSTEM_INFO_AGENT_PROMPT,
            config=config,
        )


__all__ = ["SystemInfoAgent"]