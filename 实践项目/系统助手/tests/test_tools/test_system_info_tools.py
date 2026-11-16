"""系统信息工具组单元测试 (M-TOOL-004 ~ M-TOOL-008)。"""

from __future__ import annotations

import json

from tools.system_info.disk import get_disk_info
from tools.system_info.network import get_network_info
from tools.system_info.memory import get_memory_info
from tools.system_info.process import get_process_info
from tools.system_info.device import get_device_info


def test_disk_tool():
    """M-TOOL-004: 返回 JSON 字符串，含磁盘信息。"""
    data = json.loads(get_disk_info())
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "device" in data[0]


def test_network_tool():
    """M-TOOL-005: 返回 JSON 字符串，含网卡信息。"""
    data = json.loads(get_network_info())
    assert isinstance(data, list)
    assert len(data) >= 1


def test_memory_tool():
    """M-TOOL-006: 返回 JSON 字符串，含内存信息。"""
    data = json.loads(get_memory_info())
    assert "physical" in data
    assert "swap" in data


def test_process_tool():
    """M-TOOL-007: 返回 JSON 字符串，含进程列表。"""
    data = json.loads(get_process_info())
    assert isinstance(data, list)
    assert all("pid" in p and "name" in p for p in data)


def test_device_tool():
    """M-TOOL-008: 返回 JSON 字符串，含设备信息。"""
    data = json.loads(get_device_info())
    assert isinstance(data, dict)