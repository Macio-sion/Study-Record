"""终端命令执行器。

提供命令安全校验（黑名单 + 链式操作符）与子进程执行（带超时控制）。
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CommandResult:
    """命令执行结果。"""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False


class TerminalExecutor:
    """终端命令执行器。"""

    # 危险命令黑名单
    BLOCKED_PATTERNS = [
        "format",           # 格式化磁盘
        "del /f /s",        # 强制递归删除
        "rm -rf /",         # Linux 危险命令
        "rd /s /q c:",      # 删除 C 盘
        "shutdown /s",      # 关机
        "shutdown /r",      # 重启
        "diskpart",         # 磁盘分区
        "bcdedit",          # 引导配置
    ]

    # 危险链式操作符
    CHAIN_OPERATORS = ["&&", "||", "|", ";"]

    # 允许使用管道符的安全命令（白名单）
    SAFE_PIPE_COMMANDS = {"echo", "type", "find", "findstr", "dir", "more", "sort"}

    def __init__(self, blocked_patterns: Optional[list] = None, command_timeout: int = 10) -> None:
        self.blocked_patterns = blocked_patterns if blocked_patterns is not None else self.BLOCKED_PATTERNS
        self.command_timeout = command_timeout

    @classmethod
    def _validate_command(cls, command: str) -> Tuple[bool, str]:
        """校验命令安全性，返回 (是否安全, 原因)。

        静态方法，便于测试直接调用。
        """
        cmd_lower = command.lower()

        for pattern in cls.BLOCKED_PATTERNS:
            if pattern in cmd_lower:
                return False, f"命令包含危险操作: {pattern}"

        for op in cls.CHAIN_OPERATORS:
            if op in command:
                # 仅白名单命令允许使用管道符；其余链式操作符（&&、||、;）一律拦截
                if op == "|":
                    first_token = cmd_lower.strip().split()[0] if cmd_lower.strip() else ""
                    if first_token in cls.SAFE_PIPE_COMMANDS:
                        continue
                return False, f"命令包含链式操作符: {op}"

        return True, ""

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """实例级命令校验（支持自定义黑名单）。"""
        cmd_lower = command.lower()

        for pattern in self.blocked_patterns:
            if pattern in cmd_lower:
                return False, f"命令包含危险操作: {pattern}"

        for op in self.CHAIN_OPERATORS:
            if op in command:
                # 仅白名单命令允许使用管道符；其余链式操作符（&&、||、;）一律拦截
                if op == "|":
                    first_token = cmd_lower.strip().split()[0] if cmd_lower.strip() else ""
                    if first_token in self.SAFE_PIPE_COMMANDS:
                        continue
                return False, f"命令包含链式操作符: {op}"

        return True, ""

    def execute_command(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """执行命令（Windows 中文编码 gbk + 替换无法解码字符）。"""
        timeout = timeout if timeout is not None else self.command_timeout
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="gbk",
                errors="replace",
            )
            return CommandResult(
                stdout=process.stdout or "",
                stderr=process.stderr or "",
                exit_code=process.returncode,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(stderr="命令执行超时", exit_code=-1, timed_out=True)
        except Exception as exc:
            return CommandResult(stderr=f"命令执行失败: {exc}", exit_code=-1)


__all__ = ["TerminalExecutor", "CommandResult"]