"""注册表工具 - 打开注册表编辑器。"""

from __future__ import annotations

import json

from system.registry_access import RegistryAccess
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.REGISTRY,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.HIGH,
)
def open_registry_editor() -> str:
    """打开注册表编辑器（高风险操作，需用户确认）。"""
    ok = RegistryAccess.open_registry_editor()
    if ok:
        return json.dumps({
            "success": True,
            "message": "注册表编辑器已打开。警告：修改注册表可能导致系统不稳定，请谨慎操作。",
        }, ensure_ascii=False)
    return json.dumps({"success": False, "message": "打开注册表编辑器失败"}, ensure_ascii=False)