"""终端工具 - 修改终端样式。"""

from __future__ import annotations

import json
import os
from typing import Optional

from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.TERMINAL,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.LOW,
)
def set_terminal_style(
    encoding: Optional[str] = None,
    font_size: Optional[int] = None,
    background_color: Optional[str] = None,
    text_color: Optional[str] = None,
) -> str:
    """修改终端样式（通过 Windows Terminal settings.json，仅影响 Windows Terminal）。

    Args:
        encoding: 编码格式
        font_size: 字体大小
        background_color: 背景颜色
        text_color: 文本颜色
    """
    candidate_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows Terminal\settings.json"),
    ]
    settings_path = next((p for p in candidate_paths if os.path.exists(p)), None)

    if settings_path is None:
        return json.dumps(
            {"success": False, "message": "未找到 Windows Terminal 配置文件，请确认已安装 Windows Terminal。"},
            ensure_ascii=False,
        )

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        defaults = settings.setdefault("profiles", {}).setdefault("defaults", {})
        modified = []

        if encoding:
            defaults["commandline"] = f"chcp {encoding}"
            modified.append(f"编码格式: {encoding}")
        if font_size:
            defaults["fontSize"] = font_size
            modified.append(f"字体大小: {font_size}")
        if background_color:
            defaults["background"] = background_color
            modified.append(f"背景颜色: {background_color}")
        if text_color:
            defaults["foreground"] = text_color
            modified.append(f"文本颜色: {text_color}")

        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        return json.dumps(
            {"success": True, "message": f"终端样式已更新: {', '.join(modified)}（重启终端生效）"},
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps({"success": False, "message": f"修改样式失败: {exc}"}, ensure_ascii=False)