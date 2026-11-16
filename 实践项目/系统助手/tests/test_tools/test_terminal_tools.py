"""终端工具组单元测试 (M-TOOL-015 ~ M-TOOL-018)。"""

from __future__ import annotations

import json
import os
import subprocess

from tools.terminal.open_terminal import open_terminal
from tools.terminal.execute_command import execute_command
from tools.terminal.terminal_style import set_terminal_style


def test_open_terminal_success(monkeypatch):
    """M-TOOL-015: 打开终端窗口返回 success=True。"""

    class FakePopen:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    data = json.loads(open_terminal())
    assert data["success"] is True


def test_execute_safe_command():
    """M-TOOL-017: 执行安全命令返回 stdout。"""
    data = json.loads(execute_command("echo test"))
    assert data["success"] is True
    assert "test" in data["stdout"]


def test_execute_dangerous_command():
    """M-TOOL-018: 危险命令被拦截。"""
    data = json.loads(execute_command("format C:"))
    assert data["success"] is False
    assert "拦截" in data["message"]


def test_set_terminal_style_not_found(monkeypatch):
    """终端样式: 未找到 Windows Terminal 配置文件。"""
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    data = json.loads(set_terminal_style(font_size=16))
    assert data["success"] is False


def test_set_terminal_style_success(tmp_path, monkeypatch):
    """M-TOOL-016: 修改 settings.json 成功。"""
    settings = tmp_path / "settings.json"
    settings.write_text('{"profiles": {}}', encoding="utf-8")

    mkpath = lambda p: str(settings)  # noqa: E731
    monkeypatch.setattr(os.path, "expandvars", mkpath)
    data = json.loads(set_terminal_style(font_size=16))
    assert data["success"] is True

    content = json.loads(settings.read_text(encoding="utf-8"))
    assert content["profiles"]["defaults"]["fontSize"] == 16