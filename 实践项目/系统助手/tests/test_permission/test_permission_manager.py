"""权限管理器单元测试 (M-PERM-001 ~ M-PERM-006)。"""

from __future__ import annotations

from permission.permission_manager import PermissionManager
from utils.constants import RiskLevel


def test_read_permission_passes():
    """M-PERM-001: READ（LOW 风险）直接放行。"""
    pm = PermissionManager()
    assert pm.check_permission("get_disk_info", "查看磁盘", RiskLevel.LOW) is True


def test_no_confirm_when_disabled():
    """M-PERM-004 补充: 关闭危险操作确认时自动放行。"""
    pm = PermissionManager(confirm_dangerous_ops=False)
    assert pm.check_permission("empty_recycle_bin", "清空回收站", RiskLevel.HIGH) is True


def test_confirm_approved(monkeypatch):
    """M-PERM-002/003: 用户确认放行。"""
    pm = PermissionManager()

    def on_confirm(action, desc, risk):
        pm.resolve_confirmation(True)

    pm.signal_bus.confirm_requested.connect(on_confirm)
    try:
        assert pm.check_permission("stop_app", "关闭应用", RiskLevel.MEDIUM) is True
    finally:
        pm.signal_bus.confirm_requested.disconnect(on_confirm)


def test_confirm_rejected(monkeypatch):
    """M-PERM-002 补充: 用户取消则拒绝。"""
    pm = PermissionManager()

    def on_confirm(action, desc, risk):
        pm.resolve_confirmation(False)

    pm.signal_bus.confirm_requested.connect(on_confirm)
    try:
        assert pm.check_permission("stop_app", "关闭应用", RiskLevel.MEDIUM) is False
    finally:
        pm.signal_bus.confirm_requested.disconnect(on_confirm)


def test_approve_session():
    """M-PERM-005: 会话批准后无需再次确认。"""
    pm = PermissionManager()
    pm.approve_session("stop_app")
    assert "stop_app" in pm.session_approved
    assert pm.check_permission("stop_app", "关闭应用", RiskLevel.MEDIUM) is True


def test_revoke_session():
    """M-PERM-006: 撤销批准后从集合移除。"""
    pm = PermissionManager()
    pm.approve_session("stop_app")
    pm.revoke_session("stop_app")
    assert "stop_app" not in pm.session_approved


def test_clear_session():
    """补充: 清空会话批准记录。"""
    pm = PermissionManager()
    pm.approve_session("a")
    pm.approve_session("b")
    pm.clear_session()
    assert pm.session_approved == set()