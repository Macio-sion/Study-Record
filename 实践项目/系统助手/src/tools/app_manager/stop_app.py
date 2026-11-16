"""应用管理工具 - 关闭应用。"""

from __future__ import annotations

import json

from system.app_control import AppController
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.APP_MANAGER,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.MEDIUM,
)
def stop_application(app_name: str, force: bool = False) -> str:
    """关闭应用（默认安全终止，可选强制终止，需用户确认）。

    Args:
        app_name: 应用名称（模糊匹配）
        force: 是否强制终止
    """
    result = AppController.stop_app(app_name, force)
    return json.dumps(result, ensure_ascii=False)