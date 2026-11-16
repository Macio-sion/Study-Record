"""审计日志。

以 JSON 追加写入方式记录系统变更操作，字段包括：
timestamp / tool / action / params / result / user_confirmed。
采用追加（append）模式，不可覆盖历史记录。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class AuditLogger:
    """审计日志记录器。"""

    def __init__(self, log_dir: Optional[Path] = None) -> None:
        self.log_path = Path(log_dir) if log_dir else (Path(__file__).resolve().parents[2] / "data")
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_path / "audit.log"

    def log_operation(
        self,
        tool_name: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        result: str = "",
        user_confirmed: bool = False,
    ) -> None:
        """记录一条操作审计日志。"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "action": action,
            "params": params or {},
            "result": (result or "")[:500],
            "user_confirmed": user_confirmed,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


__all__ = ["AuditLogger"]