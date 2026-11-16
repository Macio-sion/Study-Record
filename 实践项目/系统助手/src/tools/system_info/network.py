"""系统信息工具 - 网络信息。"""

from __future__ import annotations

from system import sys_info
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.SYSTEM_INFO,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def get_network_info(interface: str = "all") -> str:
    """获取网络信息（IP、网卡状态、流量统计）。

    Args:
        interface: 网卡名称，或 "all" 获取全部

    Returns:
        JSON 格式的网络信息
    """
    return sys_info.get_network_info(interface)