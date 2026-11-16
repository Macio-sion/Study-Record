"""系统信息工具 - 磁盘信息。"""

from __future__ import annotations

from system import sys_info
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.SYSTEM_INFO,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def get_disk_info(drive_letter: str = "all") -> str:
    """获取磁盘信息。

    Args:
        drive_letter: 盘符（如 "C"），或 "all" 获取全部分区

    Returns:
        JSON 格式的磁盘信息
    """
    return sys_info.get_disk_info(drive_letter)