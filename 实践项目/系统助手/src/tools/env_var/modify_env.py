"""环境变量工具 - 修改环境变量。"""

from __future__ import annotations

import json

from system.env_var_ops import EnvScope, EnvVarOps
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.ENV_VAR,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.HIGH,
)
def set_env_var(name: str, value: str = "", scope: str = "user", action: str = "set") -> str:
    """修改环境变量（高风险操作，需用户确认）。

    Args:
        name: 变量名
        value: 变量值（action=delete 时忽略）
        scope: 作用域 (user | system)
        action: 操作类型 (set | delete | append)
    """
    try:
        scope_enum = EnvScope.USER if scope == "user" else EnvScope.SYSTEM

        if action == "set":
            success = EnvVarOps.set_env_var(name, value, scope_enum)
            msg = f"已设置 {scope} 环境变量 {name}={value}"
        elif action == "delete":
            success = EnvVarOps.delete_env_var(name, scope_enum)
            msg = f"已删除 {scope} 环境变量 {name}"
        elif action == "append":
            current = EnvVarOps.get_env_var(name)
            new_value = f"{current};{value}" if current else value
            success = EnvVarOps.set_env_var(name, new_value, scope_enum)
            msg = f"已追加 {scope} 环境变量 {name} += {value}"
        else:
            return json.dumps({"success": False, "message": f"未知操作: {action}"}, ensure_ascii=False)

        return json.dumps({
            "success": success,
            "message": msg + " (可能需要重启应用生效)",
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "message": f"操作失败: {exc}"}, ensure_ascii=False)