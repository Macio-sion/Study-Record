"""审计日志单元测试 (M-PERM-007 ~ M-PERM-008)。"""

from __future__ import annotations

import json

from permission.audit_log import AuditLogger


def test_log_operation_writes_entry(tmp_path):
    """M-PERM-007: 记录操作并写入 audit.log（JSON 追加）。"""
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_operation(
        tool_name="stop_application",
        action="关闭应用",
        params={"app_name": "notepad"},
        result="success",
        user_confirmed=True,
    )

    log_file = tmp_path / "audit.log"
    assert log_file.exists()

    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])


def test_log_entry_fields_complete(tmp_path):
    """M-PERM-008: 记录字段完整 (timestamp/tool/action/params/result/user_confirmed)。"""
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_operation("empty_recycle_bin", "清空回收站", result="ok", user_confirmed=True)

    entry = json.loads((tmp_path / "audit.log").read_text(encoding="utf-8").strip())
    for field in ("timestamp", "tool", "action", "params", "result", "user_confirmed"):
        assert field in entry


def test_log_operation_appends(tmp_path):
    """补充: 追加写入，不覆盖历史。"""
    logger = AuditLogger(log_dir=tmp_path)
    logger.log_operation("a", "第一项")
    logger.log_operation("b", "第二项")
    lines = (tmp_path / "audit.log").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2