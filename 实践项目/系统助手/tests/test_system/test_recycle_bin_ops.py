"""回收站操作模块单元测试 (M-SYS-024 ~ M-SYS-026)。"""

from __future__ import annotations

import pytest

from system.recycle_bin_ops import RecycleBinOps


class _FakeShell32:
    def __init__(self, retval=0):
        self.retval = retval

    def SHEmptyRecycleBinW(self, *args, **kwargs):
        return self.retval


class _FakeWindll:
    def __init__(self, retval=0):
        self.shell32 = _FakeShell32(retval)


def test_empty_recycle_bin_success(monkeypatch):
    """M-SYS-024: SHEmptyRecycleBinW 返回 S_OK 时清空成功。"""
    monkeypatch.setattr("ctypes.windll", _FakeWindll(0))
    assert RecycleBinOps.empty_recycle_bin() is True


def test_empty_recycle_bin_failure(monkeypatch):
    """M-SYS-024 补充: 非零返回值表示失败。"""
    monkeypatch.setattr("ctypes.windll", _FakeWindll(1))
    assert RecycleBinOps.empty_recycle_bin() is False


def test_recycle_file_not_exists():
    """M-SYS-026: 文件不存在抛出 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        RecycleBinOps.recycle_file(r"C:\__no_such_file__.txt")