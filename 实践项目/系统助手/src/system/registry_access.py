"""注册表访问。

提供打开注册表编辑器、读写键值、删除键的能力。
"""

from __future__ import annotations

import subprocess
from typing import Any, Optional


class RegistryAccess:
    """注册表访问封装。"""

    @staticmethod
    def open_registry_editor() -> bool:
        """打开注册表编辑器 (regedit.exe)。"""
        try:
            subprocess.Popen("regedit.exe")
            return True
        except Exception:
            return False

    @staticmethod
    def read_value(
        hive: str,
        sub_key: str,
        value_name: str,
    ) -> Optional[Any]:
        """读取注册表键值。

        Args:
            hive: 根键名，如 "HKEY_CURRENT_USER"
            sub_key: 子键路径
            value_name: 值名称
        """
        import winreg

        hkey_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        }
        root = hkey_map.get(hive.upper())
        if root is None:
            raise ValueError(f"未知根键: {hive}")

        try:
            with winreg.OpenKey(root, sub_key) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
        except FileNotFoundError:
            return None
        except OSError:
            return None

    @staticmethod
    def write_value(hive: str, sub_key: str, value_name: str, value: Any) -> bool:
        """写入注册表键值（字符串/整型）。"""
        import winreg

        hkey_map = {
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        }
        root = hkey_map.get(hive.upper())
        if root is None:
            raise ValueError(f"未知根键: {hive}")

        value_type = winreg.REG_DWORD if isinstance(value, int) else winreg.REG_SZ
        try:
            with winreg.OpenKey(root, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, value_name, 0, value_type, value)
            return True
        except OSError:
            return False

    @staticmethod
    def delete_value(hive: str, sub_key: str, value_name: str) -> bool:
        """删除注册表键值。"""
        import winreg

        hkey_map = {
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        }
        root = hkey_map.get(hive.upper())
        if root is None:
            raise ValueError(f"未知根键: {hive}")

        try:
            with winreg.OpenKey(root, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, value_name)
            return True
        except OSError:
            return False


__all__ = ["RegistryAccess"]