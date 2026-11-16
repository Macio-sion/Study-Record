"""注册表工具单元测试 (M-TOOL-019)。"""

from __future__ import annotations

import json

from system.registry_access import RegistryAccess
from tools.registry.open_registry import open_registry_editor


def test_open_registry_editor_success(monkeypatch):
    """M-TOOL-019: 返回 success=True。"""
    monkeypatch.setattr(RegistryAccess, "open_registry_editor", staticmethod(lambda: True))
    data = json.loads(open_registry_editor())
    assert data["success"] is True


def test_open_registry_editor_failure(monkeypatch):
    """M-TOOL-019 补充: 打开失败返回 success=False。"""
    monkeypatch.setattr(RegistryAccess, "open_registry_editor", staticmethod(lambda: False))
    data = json.loads(open_registry_editor())
    assert data["success"] is False