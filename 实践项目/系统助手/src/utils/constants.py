"""项目常量定义模块。

定义系统小助手中跨模块共享的枚举常量：
- TaskType：Supervisor 意图分类结果
- ToolCategory：工具分类
- PermissionLevel：权限分级（READ/WRITE/DANGEROUS 三级）
- RiskLevel：操作风险等级（LOW/MEDIUM/HIGH）
"""

from __future__ import annotations

from enum import Enum, IntEnum


class TaskType(str, Enum):
    """智能体任务类型（Supervisor 意图识别输出）。"""

    SYSTEM_INFO = "SYSTEM_INFO"
    APP_MANAGER = "APP_MANAGER"
    TERMINAL = "TERMINAL"
    REGISTRY = "REGISTRY"
    ENV_VAR = "ENV_VAR"
    RECYCLE_BIN = "RECYCLE_BIN"
    KNOWLEDGE_QA = "KNOWLEDGE_QA"
    GENERAL_CHAT = "GENERAL_CHAT"


class ToolCategory(str, Enum):
    """工具分类。"""

    SYSTEM_INFO = "system_info"
    APP_MANAGER = "app_manager"
    TERMINAL = "terminal"
    REGISTRY = "registry"
    RECYCLE_BIN = "recycle_bin"
    ENV_VAR = "env_var"
    KNOWLEDGE = "knowledge"


class PermissionLevel(str, Enum):
    """权限分级。

    READ      只读操作，无需确认。
    WRITE     涉及系统变更，需要用户确认。
    DANGEROUS 高风险操作，需要二次确认。
    """

    READ = "read"
    WRITE = "write"
    DANGEROUS = "dangerous"


class RiskLevel(IntEnum):
    """操作风险等级（数值越大风险越高）。"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


__all__ = ["TaskType", "ToolCategory", "PermissionLevel", "RiskLevel"]