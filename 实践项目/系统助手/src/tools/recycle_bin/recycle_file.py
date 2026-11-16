"""回收站工具 - 回收文件。"""

from __future__ import annotations

import json

from system.recycle_bin_ops import RecycleBinOps
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.APP_MANAGER,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.MEDIUM,
)
def recycle_file(file_path: str) -> str:
    """将指定文件移入回收站（需用户确认）。

    Args:
        file_path: 文件路径
    """
    try:
        success = RecycleBinOps.recycle_file(file_path)
        return json.dumps({
            "success": success,
            "message": "文件已移入回收站" if success else "回收文件失败",
        }, ensure_ascii=False)
    except FileNotFoundError as exc:
        return json.dumps({"success": False, "message": f"操作失败: {exc}"}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "message": f"操作失败: {exc}"}, ensure_ascii=False)