"""系统信息工具 - 设备信息。"""

from __future__ import annotations

from system import sys_info
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.SYSTEM_INFO,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def get_device_info() -> str:
    """获取设备信息（CPU、GPU、主板、BIOS）。"""
    return sys_info.get_device_info()