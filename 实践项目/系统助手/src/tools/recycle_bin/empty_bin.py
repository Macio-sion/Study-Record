"""回收站工具 - 清空回收站。"""

from __future__ import annotations

import json

from system.recycle_bin_ops import RecycleBinOps
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.APP_MANAGER,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.HIGH,
)
def empty_recycle_bin() -> str:
    """清空回收站（高风险操作，需二次确认）。"""
    try:
        success = RecycleBinOps.empty_recycle_bin()
        return json.dumps({
            "success": success,
            "message": "回收站已清空" if success else "清空回收站失败",
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "message": f"操作失败: {exc}"}, ensure_ascii=False)