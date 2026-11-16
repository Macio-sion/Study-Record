"""回收站工具组单元测试 (M-TOOL-020 ~ M-TOOL-021)。"""

from __future__ import annotations

import json

from system.recycle_bin_ops import RecycleBinOps
from tools.recycle_bin.empty_bin import empty_recycle_bin
from tools.recycle_bin.recycle_file import recycle_file


def test_empty_recycle_bin_success(monkeypatch):
    """M-TOOL-020: 清空回收站返回 success=True。"""
    monkeypatch.setattr(RecycleBinOps, "empty_recycle_bin", staticmethod(lambda: True))
    data = json.loads(empty_recycle_bin())
    assert data["success"] is True


def test_recycle_file_success(monkeypatch):
    """M-TOOL-021: 文件移入回收站成功。"""
    monkeypatch.setattr(RecycleBinOps, "recycle_file", staticmethod(lambda p: True))
    data = json.loads(recycle_file("C:/some/file.txt"))
    assert data["success"] is True


def test_recycle_file_not_exists():
    """M-TOOL-021 补充: 文件不存在返回 success=False。"""
    data = json.loads(recycle_file("C:/__no_such_file_path__.txt"))
    assert data["success"] is False