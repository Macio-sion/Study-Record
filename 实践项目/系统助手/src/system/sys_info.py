"""系统信息采集。

封装 psutil + WMI，提供磁盘、网络、内存、进程、设备五类信息采集。
所有方法返回 JSON 字符串，供工具层直接消费。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import psutil


def _gb(value: float) -> float:
    return round(value / (1024 ** 3), 2)


def get_disk_info(drive_letter: str = "all") -> str:
    """获取磁盘信息。

    Args:
        drive_letter: 盘符（如 "C"），或 "all" 获取全部分区。
    """
    result: List[Dict[str, Any]] = []
    for part in psutil.disk_partitions():
        if drive_letter != "all" and not part.device.upper().startswith(drive_letter.upper()):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            result.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_gb": _gb(usage.total),
                "used_gb": _gb(usage.used),
                "free_gb": _gb(usage.free),
                "percent_used": usage.percent,
            })
        except (PermissionError, OSError):
            result.append({"device": part.device, "error": "无权限访问或无介质"})
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_network_info(interface: str = "all") -> str:
    """获取网络信息（IP、网卡状态、流量统计）。"""
    result: List[Dict[str, Any]] = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    try:
        io_counters = psutil.net_io_counters(pernic=True)
    except Exception:
        io_counters = {}

    for name in addrs:
        if interface != "all" and name != interface:
            continue

        is_up = bool(stats[name].isup) if name in stats else False
        interface_info: Dict[str, Any] = {
            "name": name,
            "is_up": is_up,
            "addresses": [],
            "io_counters": {},
        }

        for addr in addrs[name]:
            interface_info["addresses"].append({
                "family": str(addr.family),
                "address": addr.address,
                "netmask": addr.netmask,
                "broadcast": addr.broadcast,
            })

        if name in io_counters:
            io = io_counters[name]
            interface_info["io_counters"] = {
                "bytes_sent_mb": round(io.bytes_sent / (1024 ** 2), 2),
                "bytes_recv_mb": round(io.bytes_recv / (1024 ** 2), 2),
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
            }

        result.append(interface_info)

    return json.dumps(result, ensure_ascii=False, indent=2)


def get_memory_info() -> str:
    """获取内存信息（物理内存 + 虚拟内存/Swap）。"""
    virtual = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return json.dumps({
        "physical": {
            "total_gb": _gb(virtual.total),
            "available_gb": _gb(virtual.available),
            "used_gb": _gb(virtual.used),
            "percent_used": virtual.percent,
        },
        "swap": {
            "total_gb": _gb(swap.total),
            "used_gb": _gb(swap.used),
            "percent_used": swap.percent,
        },
    }, ensure_ascii=False, indent=2)


def get_process_info(name_filter: str = "", sort_by: str = "cpu", top_n: int = 20) -> str:
    """获取进程信息（可按名称过滤、按 CPU/内存/PID 排序）。"""
    processes: List[Dict[str, Any]] = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = proc.info
            if name_filter and name_filter.lower() not in (info['name'] or '').lower():
                continue

            connections: List[Dict[str, Any]] = []
            try:
                for conn in proc.net_connections(kind='inet'):
                    connections.append({
                        "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        "status": conn.status,
                    })
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            processes.append({
                "pid": info['pid'],
                "name": info['name'] or "",
                "cpu_percent": info['cpu_percent'],
                "memory_percent": round(info['memory_percent'] or 0.0, 2),
                "status": info['status'],
                "connections": connections[:5],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key_map = {"cpu": "cpu_percent", "memory": "memory_percent", "pid": "pid"}
    processes.sort(key=lambda x: x.get(key_map.get(sort_by, "cpu_percent"), 0), reverse=True)

    return json.dumps(processes[:top_n], ensure_ascii=False, indent=2)


def get_device_info() -> str:
    """获取设备信息（CPU、GPU、主板、BIOS）。"""
    result: Dict[str, Any] = {}

    try:
        import wmi
        c = wmi.WMI()

        result["cpu"] = [{
            "name": cpu.Name.strip() if cpu.Name else "",
            "cores": cpu.NumberOfCores,
            "logical_processors": cpu.NumberOfLogicalProcessors,
            "max_clock_mhz": cpu.MaxClockSpeed,
        } for cpu in c.Win32_Processor()]

        result["gpu"] = [{
            "name": gpu.Name,
            "driver_version": gpu.DriverVersion,
            "vram_mb": int(gpu.AdapterRAM) // (1024 ** 2) if gpu.AdapterRAM else 0,
        } for gpu in c.Win32_VideoController()]

        for board in c.Win32_BaseBoard():
            result["motherboard"] = {
                "manufacturer": board.Manufacturer,
                "product": board.Product,
            }
            break

        for bios in c.Win32_BIOS():
            release = bios.ReleaseDate
            result["bios"] = {
                "manufacturer": bios.Manufacturer,
                "version": bios.Version,
                "release_date": (release.split('.')[0] if release else "Unknown"),
            }
            break

        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:  # WMI 不可用等场景
        return json.dumps({"error": f"设备信息采集失败: {exc}"}, ensure_ascii=False)


__all__ = [
    "get_disk_info",
    "get_network_info",
    "get_memory_info",
    "get_process_info",
    "get_device_info",
]