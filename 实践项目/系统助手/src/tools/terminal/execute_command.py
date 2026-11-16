"""终端工具 - 执行命令。"""

from __future__ import annotations

import json

from system.terminal_executor import TerminalExecutor
from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.TERMINAL,
    permission=PermissionLevel.WRITE,
    risk_level=RiskLevel.HIGH,
)
def execute_command(command: str) -> str:
    """执行终端命令（高风险操作，需用户确认）。

    安全措施：黑名单检测、链式操作符检测、超时控制、输出截断。

    Args:
        command: 要执行的命令
    """
    is_valid, reason = TerminalExecutor._validate_command(command)
    if not is_valid:
        return json.dumps({"success": False, "message": f"命令被拦截: {reason}"}, ensure_ascii=False)

    result = TerminalExecutor().execute_command(command)
    return json.dumps({
        "success": result.exit_code == 0,
        "command": command,
        "stdout": (result.stdout or "")[:10000],
        "stderr": (result.stderr or "")[:1000],
        "exit_code": result.exit_code,
    }, ensure_ascii=False)