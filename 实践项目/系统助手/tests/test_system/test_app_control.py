"""应用控制模块单元测试 (M-SYS-011 ~ M-SYS-015)。"""

from __future__ import annotations

import os
import shutil
import subprocess

from system.app_control import AppController


def test_list_installed_apps():
    """M-SYS-011: 返回已安装应用列表，元素含 name/version/publisher 字段。"""
    apps = AppController.list_installed_apps()
    assert isinstance(apps, list)
    for app in apps:
        data = app.to_dict()
        assert "name" in data
        assert "version" in data
        assert "publisher" in data


def test_list_running_apps():
    """M-SYS-012: 返回运行中应用列表，过滤系统进程。"""
    running = AppController.list_running_apps()
    assert isinstance(running, list)
    for proc in running:
        assert proc.pid > 0
        assert proc.name
        # 系统进程不应出现在运行中应用列表
        assert proc.name.lower() not in {
            "system", "system idle process", "svchost.exe", "csrss.exe",
        }


def test_start_app_existing_path(monkeypatch):
    """M-SYS-013: 已存在路径用 ShellExecute 启动，返回 success=True。"""
    opened: list = []
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    monkeypatch.setattr(os, "startfile", lambda p: opened.append(p))
    result = AppController.start_app(r"C:\Program Files\App\app.exe")
    assert result["success"] is True
    assert opened == [r"C:\Program Files\App\app.exe"]


def test_start_app_command_name(monkeypatch):
    """M-SYS-013: 命令名在 PATH 解析后以列表参数启动，返回 success=True 且含 pid。"""

    class FakePopen:
        pid = 4242

        def __init__(self, args, **kwargs):
            self.args = args

    monkeypatch.setattr(os.path, "exists", lambda p: False)
    monkeypatch.setattr(shutil, "which", lambda p: r"C:\Windows\System32\notepad.exe")
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    result = AppController.start_app("notepad.exe")
    assert result["success"] is True
    assert result["pid"] == 4242


def test_start_app_not_found(monkeypatch):
    """M-SYS-013 补充: 命令名无法解析时返回 success=False。"""
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    monkeypatch.setattr(shutil, "which", lambda p: None)
    result = AppController.start_app("no_such_app_xyz.exe")
    assert result["success"] is False
    assert "未找到" in result["message"]


def test_start_app_failure(monkeypatch):
    """M-SYS-013 补充: 启动异常时返回 success=False。"""

    def _raise(*args, **kwargs):
        raise OSError("启动失败")

    monkeypatch.setattr(os.path, "exists", lambda p: True)
    monkeypatch.setattr(os, "startfile", _raise)
    result = AppController.start_app(r"C:\some\broken.exe")
    assert result["success"] is False


def test_extract_exe_path_quoted_with_icon_index(monkeypatch):
    """DisplayIcon 形如 "C:\\app.exe",0 时提取出 exe 路径。"""
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    result = AppController._extract_exe_path(r'"C:\Program Files\App\app.exe",0')
    assert result == r"C:\Program Files\App\app.exe"


def test_extract_exe_path_unquoted_with_icon_index(monkeypatch):
    """DisplayIcon 形如 C:\\app.exe,0 时提取出 exe 路径。"""
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    result = AppController._extract_exe_path(r"C:\Program Files\App\app.exe,0")
    assert result == r"C:\Program Files\App\app.exe"


def test_extract_exe_path_non_exe(monkeypatch):
    """DisplayIcon 指向 dll 时返回空串。"""
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    result = AppController._extract_exe_path(r"C:\WINDOWS\system32\imageres.dll,-100")
    assert result == ""


def test_extract_exe_path_empty():
    """空 DisplayIcon 返回空串。"""
    assert AppController._extract_exe_path("") == ""


def test_start_app_resolves_from_display_name(monkeypatch):
    """M-SYS-013 补充: 传显示名时反查已安装应用的 exe 并启动。"""
    from system.app_control import AppInfo

    class FakePopen:
        pid = 777

        def __init__(self, args, **kwargs):
            self.args = args

    monkeypatch.setattr(os.path, "exists", lambda p: False)
    monkeypatch.setattr(shutil, "which", lambda p: None)
    monkeypatch.setattr(
        AppController, "list_installed_apps",
        staticmethod(lambda: [AppInfo("网易云音乐", exe_path=r"D:\CloudMusic\cloudmusic.exe")]),
    )
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    result = AppController.start_app("网易云音乐")
    assert result["success"] is True
    assert result["pid"] == 777


def test_stop_app_not_found():
    """M-SYS-014/015 补充: 关闭不存在的应用返回 success=False。"""
    result = AppController.stop_app("__no_such_app_xyz__")
    assert result["success"] is False
    assert "未找到匹配" in result["message"]


def test_stop_app_not_found_force():
    """M-SYS-015: 强制终止不存在的应用同样返回 success=False。"""
    result = AppController.stop_app("__no_such_app_xyz__", force=True)
    assert result["success"] is False