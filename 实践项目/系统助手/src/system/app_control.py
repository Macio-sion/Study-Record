"""应用控制。

提供已安装应用扫描（注册表）、运行中进程枚举、应用启动/关闭/强杀能力。
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

import psutil

# 系统进程，运行中应用列表将其过滤掉
_SYSTEM_PROCESSES = {
    "system", "system idle process", "svchost.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "services.exe", "lsass.exe", "smss.exe", "dwm.exe",
    "explorer.exe", "registry", "memory compression", "audiodg.exe",
}

# 注册表卸载信息子键
_UNINSTALL_KEYS = [
    (0x80000002, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),  # HKLM
    (0x80000002, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (0x80000001, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),  # HKCU
]


@dataclass
class AppInfo:
    """已安装应用信息。"""

    name: str
    version: str = ""
    publisher: str = ""
    install_path: str = ""
    uninstall_string: str = ""
    exe_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProcessInfo:
    """运行中进程信息。"""

    pid: int
    name: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class AppController:
    """应用控制集合。"""

    @staticmethod
    def _read_reg_value(key, name: str) -> str:
        try:
            import winreg
            value, _ = winreg.QueryValueEx(key, name)
            return value if isinstance(value, str) else str(value)
        except OSError:
            return ""

    @staticmethod
    def _extract_exe_path(display_icon: str) -> str:
        """从注册表 ``DisplayIcon`` 值提取主程序 exe 路径。

        DisplayIcon 常见格式：
          ``"C:\\Program Files\\App\\app.exe",0``
          ``C:\\Program Files\\App\\app.exe,0``
          ``%ProgramFiles%\\App\\app.exe``
        仅当能解析为真实存在的 .exe 时返回路径，否则返回空串。
        """
        if not display_icon:
            return ""
        import os
        import re

        value = display_icon.strip()
        # 去掉末尾的 ",<图标索引>"（如 ",0" 或 ",-100"）
        value = re.sub(r",\s*-?\d+\s*$", "", value)
        value = value.strip().strip('"')
        value = os.path.expandvars(value)
        if value.lower().endswith(".exe") and os.path.exists(value):
            return value
        return ""

    @staticmethod
    def list_installed_apps() -> List[AppInfo]:
        """扫描注册表，返回已安装应用列表。"""
        try:
            import winreg
        except ImportError:  # 非 Windows 环境
            return []

        apps: List[AppInfo] = []
        seen: set = set()

        for hkey_const, path in _UNINSTALL_KEYS:
            try:
                key = winreg.OpenKey(hkey_const, path)
            except OSError:
                continue
            try:
                subkey_count = winreg.QueryInfoKey(key)[0]
                for i in range(subkey_count):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            name = AppController._read_reg_value(subkey, "DisplayName")
                            if not name or name in seen:
                                continue
                            seen.add(name)
                            display_icon = AppController._read_reg_value(subkey, "DisplayIcon")
                            apps.append(AppInfo(
                                name=name,
                                version=AppController._read_reg_value(subkey, "DisplayVersion"),
                                publisher=AppController._read_reg_value(subkey, "Publisher"),
                                install_path=AppController._read_reg_value(subkey, "InstallLocation"),
                                uninstall_string=AppController._read_reg_value(subkey, "UninstallString"),
                                exe_path=AppController._extract_exe_path(display_icon),
                            ))
                    except OSError:
                        continue
            finally:
                winreg.CloseKey(key)

        apps.sort(key=lambda a: a.name.lower())
        return apps

    @staticmethod
    def list_running_apps() -> List[ProcessInfo]:
        """返回运行中（有用户界面）的应用进程列表，过滤系统进程。"""
        running: List[ProcessInfo] = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                name = (info['name'] or '').lower()
                if not name or name in _SYSTEM_PROCESSES:
                    continue
                running.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    cpu_percent=info['cpu_percent'],
                    memory_percent=round(info['memory_percent'] or 0.0, 2),
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        running.sort(key=lambda p: p.cpu_percent if p.cpu_percent is not None else 0.0, reverse=True)
        return running

    @staticmethod
    def _resolve_installed_exe(name: str) -> Optional[str]:
        """按应用显示名（模糊匹配）反查已安装应用的可执行文件路径。

        找不到或无 exe_path 时返回 None。
        """
        needle = name.lower()
        for app in AppController.list_installed_apps():
            app_name = (app.name or "").lower()
            if app.exe_path and (needle in app_name or app_name in needle):
                return app.exe_path
        return None

    @staticmethod
    def start_app(app_path_or_name: str) -> Dict:
        """启动应用，返回执行结果。

        优先使用 ``os.startfile``（ShellExecute）打开已存在的文件/路径，
        正确处理含空格的路径与文件关联；否则作为命令名在 PATH 中解析，
        或按应用显示名反查已安装应用的可执行文件后启动，
        避免 ``shell=True`` 导致路径空格被拆分、且失败时被误判为成功。
        """
        import os
        import shutil

        target = (app_path_or_name or "").strip().strip('"')
        if not target:
            return {"success": False, "message": "未提供应用名称或路径"}

        try:
            # 1) 已存在的文件/目录：用 ShellExecute 打开
            if os.path.exists(target):
                os.startfile(target)
                return {"success": True, "message": f"已启动应用: {target}"}

            # 2) 含路径分隔符但文件不存在，直接判定失败
            is_path = os.path.sep in target or bool(
                os.path.altsep and os.path.altsep in target
            )
            if is_path:
                return {"success": False, "message": f"未找到应用文件: {target}"}

            # 3) 命令名：在 PATH 中解析；解析不到再按已安装应用显示名反查 exe
            resolved = shutil.which(target)
            if resolved is None:
                resolved = AppController._resolve_installed_exe(target)
            if resolved is None:
                return {"success": False, "message": f"未找到可执行程序: {target}"}

            # 已存在的路径用 ShellExecute 打开（正确处理文件关联与空格）
            if os.path.exists(resolved):
                os.startfile(resolved)
                return {"success": True, "message": f"已启动应用: {resolved}"}

            process = subprocess.Popen([resolved])
            return {"success": True, "message": f"已启动应用: {resolved}", "pid": process.pid}
        except Exception as exc:
            return {"success": False, "message": f"启动失败: {exc}"}

    @staticmethod
    def stop_app(app_name: str, force: bool = False) -> Dict:
        """关闭应用（默认安全终止，可强制终止）。"""
        stopped: List[Dict] = []
        name_lower = app_name.lower()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if name_lower in (proc.info['name'] or '').lower():
                    p = psutil.Process(proc.info['pid'])
                    if force:
                        p.kill()
                    else:
                        p.terminate()
                    stopped.append({"pid": proc.info['pid'], "name": proc.info['name']})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if stopped:
            return {"success": True, "message": f"已关闭 {len(stopped)} 个进程: {stopped}"}
        return {"success": False, "message": f"未找到匹配的应用: {app_name}"}


__all__ = ["AppController", "AppInfo", "ProcessInfo"]