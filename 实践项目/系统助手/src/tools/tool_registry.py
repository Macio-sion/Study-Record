"""工具注册表。

基于装饰器将普通函数注册为 LangChain Tool，并记录分类、权限与风险等级元数据。
注册后的工具可通过本注册表按分类或整体获取，供 Worker Agent 绑定使用。

> 说明：设计文档中本模块名为 ``tools/registry.py``，但为避免与工具分类目录
> ``tools/registry/``（注册表编辑器工具组）命名冲突，实际模块命名为
> ``tool_registry.py``。``tools/registry/`` 包会重导出本模块的 ``ToolRegistry``。
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from langchain_core.tools import BaseTool
from langchain_core.tools import tool as _lc_tool

from utils.constants import PermissionLevel, RiskLevel, ToolCategory


@dataclass
class ToolMeta:
    """工具元数据。"""

    name: str
    category: ToolCategory
    permission: PermissionLevel
    risk_level: RiskLevel
    description: str
    func: Callable


class PermissionDeniedError(Exception):
    """权限被拒绝（用户取消确认）时抛出。"""


class ToolRegistry:
    """工具注册中心。"""

    _tools: Dict[str, BaseTool] = {}
    _meta: Dict[str, ToolMeta] = {}

    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls,
        category: ToolCategory,
        permission: PermissionLevel,
        risk_level: RiskLevel,
        name: Optional[str] = None,
    ) -> Callable:
        """注册装饰器。

        返回原始函数（保持可直接调用），同时将对应的 LangChain Tool
        存入注册表。实际执行时若需要权限确认，会先经过权限门控。
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__

            @functools.wraps(func)
            def _gated(*args: Any, **kwargs: Any):
                if cls._requires_confirmation(permission, risk_level):
                    from permission.permission_manager import get_permission_manager
                    pm = get_permission_manager()
                    if not pm.check_permission(tool_name, (func.__doc__ or "").strip(), risk_level):
                        raise PermissionDeniedError(f"操作已被用户取消: {tool_name}")
                return func(*args, **kwargs)

            lc_tool = _lc_tool(_gated)
            cls._tools[tool_name] = lc_tool
            cls._meta[tool_name] = ToolMeta(
                name=tool_name,
                category=category,
                permission=permission,
                risk_level=risk_level,
                description=(func.__doc__ or "").strip(),
                func=func,
            )
            # 返回原始函数，保证模块级名称仍是可直接调用的普通函数
            return func

        return decorator

    @staticmethod
    def _requires_confirmation(permission: PermissionLevel, risk_level: RiskLevel) -> bool:
        return permission != PermissionLevel.READ

    # ------------------------------------------------------------------
    @classmethod
    def get_all_tools(cls) -> List[BaseTool]:
        """获取全部已注册工具。"""
        return list(cls._tools.values())

    @classmethod
    def get_tools_by_category(cls, category: ToolCategory) -> List[BaseTool]:
        """按分类获取工具。"""
        return [t for name, t in cls._tools.items() if cls._meta[name].category == category]

    @classmethod
    def get_tool(cls, name: str) -> Optional[BaseTool]:
        """按名称获取工具。"""
        return cls._tools.get(name)

    @classmethod
    def get_meta(cls, name: str) -> Optional[ToolMeta]:
        """按名称获取工具元数据。"""
        return cls._meta.get(name)

    @classmethod
    def get_tool_names(cls) -> List[str]:
        """获取全部工具名称。"""
        return list(cls._tools.keys())

    @classmethod
    def get_tool_names_by_category(cls, category: ToolCategory) -> List[str]:
        """按分类获取工具名称。"""
        return [name for name, meta in cls._meta.items() if meta.category == category]

    @classmethod
    def reset(cls) -> None:
        """清空注册表（测试用）。"""
        cls._tools.clear()
        cls._meta.clear()


__all__ = ["ToolRegistry", "ToolMeta", "PermissionDeniedError"]