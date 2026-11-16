"""工具层包。

导入本包时自动加载所有工具模块，完成 LangChain Tool 注册。
通过 ``ToolRegistry`` 获取工具供 Agent 绑定。
"""

from __future__ import annotations

from tools.tool_registry import ToolMeta, ToolRegistry, PermissionDeniedError

# 导入各工具组，触发工具注册
from tools import system_info  # noqa: F401
from tools import app_manager  # noqa: F401
from tools import terminal  # noqa: F401
from tools import registry  # noqa: F401
from tools import recycle_bin  # noqa: F401
from tools import env_var  # noqa: F401
from tools import knowledge  # noqa: F401


def load_all_tools() -> None:
    """确保所有工具已加载（幂等）。"""
    # 所有工具组在 import tools 时已通过子包 __init__ 完成注册
    return None


__all__ = [
    "ToolMeta",
    "ToolRegistry",
    "PermissionDeniedError",
    "load_all_tools",
]