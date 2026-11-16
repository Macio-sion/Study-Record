"""应用管理工具 - 启动应用。"""

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
def start_application(app_path_or_name: str) -> str:
    """启动应用（真实执行启动动作，会返回启动结果）。

    参数可传应用的显示名称（如「网易云音乐」）或可执行文件完整路径（exe_path），
    工具会自动定位并启动，无需你自己拼接路径。
    """
    result = AppController.start_app(app_path_or_name)
    return json.dumps(result, ensure_ascii=False)