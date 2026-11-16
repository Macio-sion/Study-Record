"""工具注册表单元测试 (M-TOOL-001 ~ M-TOOL-003)。"""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory


def _ensure_tools():
    # 确保所有工具已注册（import tools 时触发）
    import tools  # noqa: F401
    return ToolRegistry


def test_register_decorator_registers_tool():
    """M-TOOL-001: 装饰器注册的工具进入 _tools 字典。"""
    _ensure_tools()
    tool = ToolRegistry.get_tool("get_disk_info")
    assert tool is not None
    assert isinstance(tool, BaseTool)


def test_get_tools_by_category_system_info():
    """M-TOOL-002: system_info 分类返回 5 个工具。"""
    _ensure_tools()
    tools = ToolRegistry.get_tools_by_category(ToolCategory.SYSTEM_INFO)
    names = {t.name for t in tools}
    assert names == {
        "get_disk_info", "get_network_info", "get_memory_info",
        "get_process_info", "get_device_info",
    }


def test_get_all_tools_count():
    """M-TOOL-003: 全部工具总数为 19。"""
    _ensure_tools()
    assert len(ToolRegistry.get_all_tools()) == 19


def test_category_counts():
    """补充: 各分类工具数量符合设计（回收站绑定到 app_manager）。"""
    _ensure_tools()
    assert len(ToolRegistry.get_tools_by_category(ToolCategory.APP_MANAGER)) == 6
    assert len(ToolRegistry.get_tools_by_category(ToolCategory.TERMINAL)) == 3
    assert len(ToolRegistry.get_tools_by_category(ToolCategory.REGISTRY)) == 1
    assert len(ToolRegistry.get_tools_by_category(ToolCategory.ENV_VAR)) == 2
    assert len(ToolRegistry.get_tools_by_category(ToolCategory.KNOWLEDGE)) == 2


def test_tool_metadata():
    """补充: 工具元数据记录权限与风险等级。"""
    _ensure_tools()
    meta = ToolRegistry.get_meta("get_disk_info")
    assert meta.category == ToolCategory.SYSTEM_INFO
    assert meta.permission == PermissionLevel.READ
    assert meta.risk_level == RiskLevel.LOW