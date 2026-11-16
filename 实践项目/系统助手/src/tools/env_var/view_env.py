"""环境变量工具 - 查看环境变量。"""

from __future__ import annotations

import json

from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.ENV_VAR,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def get_env_vars(name_filter: str = "") -> str:
    """查看环境变量。

    Args:
        name_filter: 变量名过滤（为空返回全部）
    """
    import os

    env_vars = dict(os.environ)
    if name_filter:
        env_vars = {k: v for k, v in env_vars.items() if name_filter.lower() in k.lower()}

    sorted_vars = dict(sorted(env_vars.items()))
    return json.dumps({"count": len(sorted_vars), "variables": sorted_vars}, ensure_ascii=False, indent=2)