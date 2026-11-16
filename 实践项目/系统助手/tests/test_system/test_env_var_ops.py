"""环境变量操作模块单元测试 (M-SYS-027 ~ M-SYS-030)。"""

from __future__ import annotations

import os

from system.env_var_ops import EnvScope, EnvVarOps

_TEMP_VAR = "SYS_ASSISTANT_TEST_TEMP"


def test_get_all_env_vars_contains_path():
    """M-SYS-027: 返回环境变量字典，含常见 PATH。"""
    result = EnvVarOps.get_all_env_vars()
    assert isinstance(result, dict)
    assert len(result) > 0
    # Windows 下 PATH 键通常为大写
    assert any(k.upper() == "PATH" for k in result)


def test_get_env_var_path():
    """M-SYS-027 补充: 获取单个变量的值。"""
    value = EnvVarOps.get_env_var(next(k for k in os.environ if k.upper() == "PATH"))
    assert isinstance(value, str)
    assert value


def test_set_and_delete_env_var():
    """M-SYS-028/029: 设置后读取生效，删除后移除（含清理）。"""
    try:
        assert EnvVarOps.set_env_var(_TEMP_VAR, "hello_test", EnvScope.USER) is True
        assert os.environ.get(_TEMP_VAR) == "hello_test"
        assert EnvVarOps.delete_env_var(_TEMP_VAR, EnvScope.USER) is True
        assert _TEMP_VAR not in os.environ
    finally:
        try:
            EnvVarOps.delete_env_var(_TEMP_VAR, EnvScope.USER)
        except Exception:
            pass


def test_set_env_var_not_exist_after_delete():
    """M-SYS-029 补充: 删除不存在变量抛出 RuntimeError。"""
    import pytest

    with pytest.raises(RuntimeError):
        EnvVarOps.delete_env_var(_TEMP_VAR, EnvScope.USER)