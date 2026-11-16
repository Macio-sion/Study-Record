"""Worker Agent 包。

导出 5 个具体 Worker Agent。
"""

from __future__ import annotations

from agent.agents.app_manager_agent import AppManagerAgent
from agent.agents.env_var_agent import EnvVarAgent
from agent.agents.registry_agent import RegistryAgent
from agent.agents.system_info_agent import SystemInfoAgent
from agent.agents.terminal_agent import TerminalAgent

__all__ = [
    "SystemInfoAgent",
    "AppManagerAgent",
    "TerminalAgent",
    "RegistryAgent",
    "EnvVarAgent",
]