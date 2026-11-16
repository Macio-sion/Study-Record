"""应用管理工具 - 应用详情。"""

from __future__ import annotations

import json

import psutil

from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@ToolRegistry.register(
    category=ToolCategory.APP_MANAGER,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def get_app_detail(app_name: str) -> str:
    """获取应用详细信息（进程、端口、协议、网络连接）。

    Args:
        app_name: 应用名称（模糊匹配）
    """
    result = {"name": app_name, "processes": []}

    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_percent', 'create_time']):
        try:
            if app_name.lower() not in (proc.info['name'] or '').lower():
                continue

            proc_info = {
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "exe_path": proc.info['exe'],
                "cpu_percent": proc.info['cpu_percent'],
                "memory_percent": round(proc.info['memory_percent'] or 0.0, 2),
                "connections": [],
            }

            try:
                for conn in proc.connections(kind='inet'):
                    proc_info["connections"].append({
                        "protocol": "TCP" if getattr(conn.type, "name", "") == "SOCK_STREAM" else "UDP",
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        "status": conn.status,
                    })
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            result["processes"].append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return json.dumps(result, ensure_ascii=False, indent=2)