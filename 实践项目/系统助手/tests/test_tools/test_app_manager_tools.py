"""应用管理工具组单元测试 (M-TOOL-009 ~ M-TOOL-014)。"""

from __future__ import annotations

import json

from tools.app_manager.list_apps import list_apps
from tools.app_manager.app_detail import get_app_detail
from tools.app_manager.start_app import start_application
from tools.app_manager.stop_app import stop_application


def test_list_apps_all():
    """M-TOOL-009: 默认返回 installed + running。"""
    data = json.loads(list_apps())
    assert "installed" in data
    assert "running" in data


def test_list_apps_installed_only():
    """M-TOOL-010: app_type=installed 仅返回 installed。"""
    data = json.loads(list_apps(app_type="installed"))
    assert "installed" in data
    assert "running" not in data


def test_list_apps_name_filter(monkeypatch):
    """M-TOOL-011: 名称过滤只返回匹配项。"""
    from system.app_control import AppController, AppInfo, ProcessInfo

    monkeypatch.setattr(
        AppController, "list_installed_apps",
        staticmethod(lambda: [
            AppInfo("Python 3.12", "3.12"), AppInfo("Notepad", "1.0"),
        ]),
    )
    monkeypatch.setattr(
        AppController, "list_running_apps",
        staticmethod(lambda: [ProcessInfo(1, "python.exe")]),
    )
    data = json.loads(list_apps(app_type="installed", name_filter="python"))
    assert [a["name"] for a in data["installed"]] == ["Python 3.12"]


def test_get_app_detail_empty():
    """M-TOOL-012: 无匹配进程返回空列表。"""
    data = json.loads(get_app_detail("__no_such_process__"))
    assert data["name"] == "__no_such_process__"
    assert data["processes"] == []


def test_start_application(monkeypatch):
    """M-TOOL-013: 返回 success=True 且含 pid。"""
    from system.app_control import AppController

    monkeypatch.setattr(
        AppController, "start_app",
        staticmethod(lambda name: {"success": True, "message": "ok", "pid": 99}),
    )
    data = json.loads(start_application("notepad.exe"))
    assert data["success"] is True
    assert data["pid"] == 99


def test_stop_application(monkeypatch):
    """M-TOOL-014: 终止进程返回 success=True。"""
    from system.app_control import AppController

    monkeypatch.setattr(
        AppController, "stop_app",
        staticmethod(lambda name, force=False: {"success": True, "message": "ok"}),
    )
    data = json.loads(stop_application("notepad"))
    assert data["success"] is True