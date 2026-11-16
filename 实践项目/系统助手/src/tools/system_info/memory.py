"""系统信息工具 - 内存信息。"""

from __future__ import annotations

from system import sys_info
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.SYSTEM_INFO,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def get_memory_info() -> str:
    """获取内存信息（物理内存 + 虚拟内存/Swap）。"""
    return sys_info.get_memory_info()