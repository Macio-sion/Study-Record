"""终端命令执行器单元测试 (M-SYS-016 ~ M-SYS-021)。"""

from __future__ import annotations

import subprocess

from system.terminal_executor import TerminalExecutor


def test_validate_safe_command():
    """M-SYS-016: 安全命令通过校验。"""
    ok, reason = TerminalExecutor._validate_command("dir")
    assert ok is True
    assert reason == ""


def test_validate_dangerous_command():
    """M-SYS-017: 黑名单命令被拦截。"""
    ok, reason = TerminalExecutor._validate_command("format C:")
    assert ok is False
    assert "format" in reason


def test_validate_chain_operator():
    """M-SYS-018: 链式操作符被拦截。"""
    ok, reason = TerminalExecutor._validate_command("dir && del")
    assert ok is False
    assert "&&" in reason


def test_validate_safe_pipe():
    """M-SYS-019: 安全管道命令放行。"""
    ok, reason = TerminalExecutor._validate_command("dir | findstr txt")
    assert ok is True
    assert reason == ""


def test_validate_unsafe_pipe():
    """M-SYS-019 补充: 非白名单管道命令被拦截。"""
    ok, reason = TerminalExecutor._validate_command("del | format")
    assert ok is False


def test_execute_simple_command():
    """M-SYS-020: 执行安全命令返回 stdout，exit_code=0。"""
    result = TerminalExecutor().execute_command("echo hello")
    assert result.exit_code == 0
    assert "hello" in result.stdout


def test_execute_command_timeout(monkeypatch):
    """M-SYS-021: 超时命令触发超时控制，不阻塞。"""

    def _fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout", 10))

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = TerminalExecutor().execute_command("sleep 100", timeout=1)
    assert result.timed_out is True
    assert result.exit_code == -1


def test_custom_blocked_patterns():
    """实例级自定义黑名单生效。"""
    executor = TerminalExecutor(blocked_patterns=["custom_danger"])
    ok, reason = executor.validate_command("custom_danger run")
    assert ok is False
    assert "custom_danger" in reason