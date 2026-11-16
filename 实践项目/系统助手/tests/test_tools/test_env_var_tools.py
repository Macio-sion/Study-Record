"""环境变量工具组单元测试 (M-TOOL-022 ~ M-TOOL-026)。"""

from __future__ import annotations

import json

from tools.env_var.view_env import get_env_vars
from tools.env_var.modify_env import set_env_var


def test_get_env_vars_contains_path():
    """M-TOOL-022: 返回环境变量 JSON，含 PATH。"""
    data = json.loads(get_env_vars())
    assert data["count"] >= 1
    keys = list(data["variables"].keys())
    assert any(k.upper() == "PATH" for k in keys)


def test_get_env_vars_filter():
    """M-TOOL-023: 名称过滤仅返回匹配变量。"""
    data = json.loads(get_env_vars(name_filter="PATH"))
    assert all("path" in k.lower() for k in data["variables"])


def test_set_env_var_unknown_action():
    """补充: 未知操作返回 success=False。"""
    data = json.loads(set_env_var("X", "1", "user", "bogus"))
    assert data["success"] is False
    assert "未知操作" in data["message"]


def test_set_env_var_set(monkeypatch):
    """M-TOOL-024: set 操作调用底层 set_env_var。"""
    from system.env_var_ops import EnvVarOps

    calls = {}
    monkeypatch.setattr(
        EnvVarOps, "set_env_var",
        lambda name, value, scope: calls.update(name=name, value=value) or True,
    )
    data = json.loads(set_env_var("MY_VAR", "hello", "user", "set"))
    assert data["success"] is True
    assert calls == {"name": "MY_VAR", "value": "hello"}


def test_set_env_var_delete(monkeypatch):
    """M-TOOL-025: delete 操作调用底层 delete_env_var。"""
    from system.env_var_ops import EnvVarOps

    monkeypatch.setattr(EnvVarOps, "delete_env_var", lambda name, scope: True)
    data = json.loads(set_env_var("MY_VAR", "", "user", "delete"))
    assert data["success"] is True


def test_set_env_var_append(monkeypatch):
    """M-TOOL-026: append 操作以分号拼接后写入。"""
    from system.env_var_ops import EnvVarOps

    captured = {}
    monkeypatch.setattr(EnvVarOps, "get_env_var", lambda name: "old")
    monkeypatch.setattr(
        EnvVarOps, "set_env_var",
        lambda name, value, scope: captured.update(value=value) or True,
    )
    data = json.loads(set_env_var("MY_VAR", "new", "user", "append"))
    assert data["success"] is True
    assert captured["value"] == "old;new"