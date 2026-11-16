"""回收站操作。

封装 Windows Shell API，提供清空回收站与将文件移入回收站的能力。
"""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


class RecycleBinOps:
    """回收站操作封装。"""

    @staticmethod
    def empty_recycle_bin() -> bool:
        """清空回收站（不显示确认/进度/声音）。"""
        try:
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(
                None, None,
                0x00000001 | 0x00000002 | 0x00000004,  # NOCONFIRMATION | NOPROGRESSUI | NOSOUND
            )
            return result == 0  # S_OK = 0
        except Exception:
            return False

    @staticmethod
    def recycle_file(file_path: str) -> bool:
        """将文件移至回收站。"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("wFunc", wintypes.UINT),
                ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR),
                ("fFlags", wintypes.WORD),
                ("fAnyOperationsAborted", ctypes.c_wchar),
                ("hNameMappings", ctypes.c_wchar),
                ("lpszProgressTitle", wintypes.LPCWSTR),
            ]

        FO_DELETE = 0x0003
        FOF_ALLOWUNDO = 0x0040       # 允许撤销（移入回收站）
        FOF_NOCONFIRMATION = 0x0010
        FOF_SILENT = 0x0004

        file_op = SHFILEOPSTRUCTW()
        file_op.hwnd = None
        file_op.wFunc = FO_DELETE
        file_op.pFrom = file_path + "\0\0"  # 需要双 null 结束
        file_op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT

        try:
            result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(file_op))
            return result == 0
        except Exception:
            return False


__all__ = ["RecycleBinOps"]