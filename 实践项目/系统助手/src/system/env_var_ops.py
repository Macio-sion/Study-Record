"""环境变量操作。

读写注册表 Environment 键持久化环境变量，并通过 WM_SETTINGCHANGE 广播变更。
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Dict, Optional


class EnvScope(Enum):
    """环境变量作用域。"""

    USER = "user"
    SYSTEM = "system"


class EnvVarOps:
    """环境变量操作封装。"""

    @staticmethod
    def _broadcast_change() -> None:
        """广播 WM_SETTINGCHANGE，通知其他进程环境变量已变更。

        使用 SendMessageTimeoutW（而非阻塞的 SendMessageW），避免某个窗口未响应
        导致广播无限期阻塞主流程。"""
        import ctypes

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        try:
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                SMTO_ABORTIFHUNG, 5000, None,
            )
        except Exception:
            pass  # 广播失败不影响主流程

    @staticmethod
    def _resolve_key(scope: EnvScope):
        import winreg

        if scope == EnvScope.USER:
            return winreg.HKEY_CURRENT_USER, r"Environment"
        return winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

    @staticmethod
    def get_all_env_vars() -> Dict[str, str]:
        """获取当前进程全部环境变量。"""
        return dict(os.environ)

    @staticmethod
    def get_env_var(name: str) -> Optional[str]:
        """获取单个环境变量的值。"""
        return os.environ.get(name)

    @staticmethod
    def set_env_var(name: str, value: str, scope: EnvScope = EnvScope.USER) -> bool:
        """设置环境变量（持久化到注册表）。"""
        import winreg

        hkey, key_path = EnvVarOps._resolve_key(scope)
        try:
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            EnvVarOps._broadcast_change()
            os.environ[name] = value
            return True
        except Exception as exc:
            raise RuntimeError(f"设置环境变量失败: {exc}")

    @staticmethod
    def delete_env_var(name: str, scope: EnvScope = EnvScope.USER) -> bool:
        """删除环境变量。"""
        import winreg

        hkey, key_path = EnvVarOps._resolve_key(scope)
        try:
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
            EnvVarOps._broadcast_change()
            os.environ.pop(name, None)
            return True
        except Exception as exc:
            raise RuntimeError(f"删除环境变量失败: {exc}")


__all__ = ["EnvVarOps", "EnvScope"]