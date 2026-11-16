"""权限管理器。

实现 READ / WRITE / DANGEROUS 三级权限：
- READ（低风险）：直接放行
- WRITE（中/高风险）：需要用户确认（弹出确认框）
- 会话内已批准的工具，本次会话不再重复确认

通过全局信号总线发出确认请求，UI 层监听后在主线程弹窗，用户确认结果
通过 ``resolve_confirmation`` 回传，运行在后台线程的 Agent 阻塞等待结果。
"""

from __future__ import annotations

import threading
from typing import Optional, Set

from utils.constants import RiskLevel
from utils.signal_bus import SignalBus

_CONFIRM_TIMEOUT_SECONDS = 120.0


class PermissionManager:
    """权限分级管理器。"""

    def __init__(
        self,
        signal_bus: Optional[SignalBus] = None,
        confirm_dangerous_ops: bool = True,
    ) -> None:
        self.signal_bus = signal_bus or SignalBus.instance()
        self.confirm_dangerous_ops = confirm_dangerous_ops
        self.session_approved: Set[str] = set()
        self._event = threading.Event()
        self._result = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def check_permission(self, tool_name: str, action_detail: str, risk_level) -> bool:
        """检查权限，返回是否允许执行。

        Args:
            tool_name: 工具名称
            action_detail: 操作描述（用于确认弹窗展示）
            risk_level: 风险等级（RiskLevel 或 int）
        """
        risk = risk_level if isinstance(risk_level, RiskLevel) else RiskLevel(int(risk_level))

        if risk == RiskLevel.LOW:
            return True
        if not self.confirm_dangerous_ops:
            # 用户关闭了「危险操作确认」，自动放行
            return True
        if tool_name in self.session_approved:
            return True
        return self._request_confirmation(tool_name, action_detail, risk)

    # ------------------------------------------------------------------
    def _request_confirmation(self, tool_name: str, action_detail: str, risk: RiskLevel) -> bool:
        with self._lock:
            self._event.clear()
            self._result = False
        # 发出确认请求信号（跨线程时由 Qt 排队到主线程处理弹窗）
        self.signal_bus.confirm_requested.emit(tool_name, action_detail, risk.value)
        self._event.wait(timeout=_CONFIRM_TIMEOUT_SECONDS)
        return self._result

    def resolve_confirmation(self, result: bool) -> None:
        """回传用户确认结果（由 UI 主线程调用）。"""
        self._result = bool(result)
        self._event.set()

    # ------------------------------------------------------------------
    # 会话批准管理
    # ------------------------------------------------------------------
    def approve_session(self, tool_name: str) -> None:
        """批准当前会话内该工具，后续无需再次确认。"""
        self.session_approved.add(tool_name)

    def revoke_session(self, tool_name: str) -> None:
        """撤销当前会话内该工具的批准。"""
        self.session_approved.discard(tool_name)

    def clear_session(self) -> None:
        """清空所有会话批准记录。"""
        self.session_approved.clear()


_instance: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """获取全局单例权限管理器。"""
    global _instance
    if _instance is None:
        _instance = PermissionManager()
    return _instance


def reset_permission_manager() -> None:
    """重置单例（测试用）。"""
    global _instance
    _instance = None


__all__ = [
    "PermissionManager",
    "get_permission_manager",
    "reset_permission_manager",
]