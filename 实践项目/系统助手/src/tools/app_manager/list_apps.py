"""应用管理工具 - 应用列表。"""

from __future__ import annotations

import json

from system.app_control import AppController
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.APP_MANAGER,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def list_apps(app_type: str = "all", name_filter: str = "") -> str:
    """查看应用列表（已安装 / 运行中 / 全部）。

    Args:
        app_type: 应用类型 (installed | running | all)
        name_filter: 名称过滤（模糊匹配）
    """
    result: dict = {}

    if app_type in ("installed", "all"):
        installed = AppController.list_installed_apps()
        if name_filter:
            installed = [a for a in installed if name_filter.lower() in a.name.lower()]
        result["installed"] = [a.to_dict() for a in installed[:50]]

    if app_type in ("running", "all"):
        running = AppController.list_running_apps()
        if name_filter:
            running = [a for a in running if name_filter.lower() in a.name.lower()]
        result["running"] = [a.to_dict() for a in running[:50]]

    return json.dumps(result, ensure_ascii=False, indent=2)