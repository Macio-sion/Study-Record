"""终端工具 - 打开终端窗口。"""

from __future__ import annotations

import json
import os
import subprocess

from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.TERMINAL,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.MEDIUM,
)
def open_terminal(working_dir: str = "") -> str:
    """打开终端窗口（需用户确认）。

    Args:
        working_dir: 工作目录（默认为用户主目录）
    """
    cwd = working_dir or os.path.expanduser("~")
    for term in ("wt.exe", "cmd.exe"):
        try:
            subprocess.Popen(term, cwd=cwd if os.path.isdir(cwd) else os.path.expanduser("~"))
            return json.dumps({"success": True, "message": f"终端窗口已打开 (工作目录: {cwd})"}, ensure_ascii=False)
        except FileNotFoundError:
            continue
        except Exception as exc:
            return json.dumps({"success": False, "message": f"打开终端失败: {exc}"}, ensure_ascii=False)
    return json.dumps({"success": False, "message": "未找到可用的终端程序"}, ensure_ascii=False)