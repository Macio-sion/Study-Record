"""注册表访问模块单元测试 (M-SYS-023)。"""

from __future__ import annotations

import subprocess

import pytest

from system.registry_access import RegistryAccess


def test_open_registry_editor_success(monkeypatch):
    """M-SYS-023: 打开注册表编辑器返回 True。"""

    class FakePopen:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    assert RegistryAccess.open_registry_editor() is True


def test_open_registry_editor_failure(monkeypatch):
    """M-SYS-023 补充: 启动失败返回 False。"""

    def _raise(*args, **kwargs):
        raise OSError("无法启动")

    monkeypatch.setattr(subprocess, "Popen", _raise)
    assert RegistryAccess.open_registry_editor() is False


def test_read_value_unknown_hive():
    """未知根键抛出 ValueError。"""
    with pytest.raises(ValueError):
        RegistryAccess.read_value("INVALID_HIVE", "sub", "value")


def test_read_value_missing_key():
    """不存在的键返回 None。"""
    assert RegistryAccess.read_value(
        "HKEY_CURRENT_USER", r"Software\__definitely_not_exists__", "NoSuchValue"
    ) is None