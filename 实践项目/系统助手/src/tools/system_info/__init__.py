"""系统信息工具组。"""

from tools.system_info.disk import get_disk_info
from tools.system_info.network import get_network_info
from tools.system_info.memory import get_memory_info
from tools.system_info.process import get_process_info
from tools.system_info.device import get_device_info

__all__ = [
    "get_disk_info",
    "get_network_info",
    "get_memory_info",
    "get_process_info",
    "get_device_info",
]