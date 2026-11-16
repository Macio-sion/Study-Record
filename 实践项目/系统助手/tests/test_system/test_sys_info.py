"""系统信息采集模块单元测试 (M-SYS-001 ~ M-SYS-010)。"""

from __future__ import annotations

import json

import pytest

from system import sys_info


@pytest.fixture
def disk_info():
    return json.loads(sys_info.get_disk_info())


def test_get_disk_info_returns_list(disk_info):
    """M-SYS-001: 返回 JSON 列表，含磁盘基本字段。"""
    assert isinstance(disk_info, list)
    assert len(disk_info) >= 1
    first = disk_info[0]
    for key in ("device", "total_gb", "used_gb", "free_gb", "percent_used"):
        assert key in first, f"缺少字段 {key}"


def test_get_disk_info_percent_range(disk_info):
    """M-SYS-001 补充: percent_used 数值在 0-100 之间。"""
    for part in disk_info:
        assert 0 <= part["percent_used"] <= 100


def test_get_disk_info_specific_drive():
    """M-SYS-002: 指定存在的盘符仅返回该盘信息。"""
    all_parts = json.loads(sys_info.get_disk_info())
    if not all_parts:
        pytest.skip("无可用磁盘分区")
    drive = all_parts[0]["device"].rstrip("\\").split(":")[0]
    filtered = json.loads(sys_info.get_disk_info(drive))
    assert all(p["device"].upper().startswith(drive.upper()) for p in filtered)
    assert len(filtered) >= 1


def test_get_disk_info_unknown_drive_returns_empty():
    """M-SYS-002 补充: 不存在的盘符返回空列表。"""
    assert json.loads(sys_info.get_disk_info("ZZZ")) == []


def test_get_disk_info_no_media():
    """M-SYS-003: 无介质驱动器不抛异常。"""
    # 直接调用不应抛出；存在 error 字段或无介质的分区时也能正常返回
    result = json.loads(sys_info.get_disk_info())
    assert isinstance(result, list)


def test_get_network_info_returns_list():
    """M-SYS-004: 返回网卡列表，含 name/addresses/io_counters。"""
    result = json.loads(sys_info.get_network_info())
    assert isinstance(result, list)
    assert len(result) >= 1
    for iface in result:
        assert "name" in iface
        assert isinstance(iface.get("addresses"), list)
        assert isinstance(iface.get("io_counters"), dict)


def test_get_network_info_filter():
    """M-SYS-005: 指定网卡仅返回该网卡。"""
    all_ifaces = json.loads(sys_info.get_network_info())
    if not all_ifaces:
        pytest.skip("无网络接口")
    name = all_ifaces[0]["name"]
    filtered = json.loads(sys_info.get_network_info(name))
    assert [i["name"] for i in filtered] == [name]


def test_get_memory_info():
    """M-SYS-006: 返回 physical 与 swap 信息，使用率在 0-100。"""
    result = json.loads(sys_info.get_memory_info())
    physical = result["physical"]
    assert "total_gb" in physical and "used_gb" in physical and "percent_used" in physical
    assert 0 <= physical["percent_used"] <= 100
    assert "swap" in result


def test_get_process_info_default():
    """M-SYS-007: 默认返回不超过 top_n 条，按 CPU 降序。"""
    result = json.loads(sys_info.get_process_info())
    assert isinstance(result, list)
    assert len(result) <= 20
    cpu_vals = [p["cpu_percent"] for p in result]
    assert cpu_vals == sorted(cpu_vals, reverse=True)


def test_get_process_info_name_filter():
    """M-SYS-008: 按名称过滤后所有结果均命中模糊匹配。"""
    result = json.loads(sys_info.get_process_info(name_filter="python"))
    assert all("python" in p["name"].lower() for p in result)


def test_get_process_info_sort_by_memory():
    """M-SYS-009: 按内存降序排列。"""
    result = json.loads(sys_info.get_process_info(sort_by="memory"))
    mem_vals = [p["memory_percent"] for p in result]
    assert mem_vals == sorted(mem_vals, reverse=True)


def test_get_device_info():
    """M-SYS-010: 返回设备信息字典（WMI 不可用时返回 error 字段也不抛异常）。"""
    result = json.loads(sys_info.get_device_info())
    assert isinstance(result, dict)
    assert ("cpu" in result) or ("error" in result)