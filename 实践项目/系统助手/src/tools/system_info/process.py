"""系统信息工具 - 进程信息。"""

from __future__ import annotations

from system import sys_info
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.SYSTEM_INFO,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def get_process_info(name_filter: str = "", sort_by: str = "cpu", top_n: int = 20) -> str:
    """获取进程信息（可按名称过滤、按 CPU/内存/PID 排序）。

    Args:
        name_filter: 进程名过滤（模糊匹配）
        sort_by: 排序方式 (cpu | memory | pid)
        top_n: 返回前 N 条
    """
    return sys_info.get_process_info(name_filter, sort_by, top_n)