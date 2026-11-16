"""知识库类型列表工具。"""

from __future__ import annotations

import json

from tools.tool_registry import ToolRegistry
from utils.constants import PermissionLevel, RiskLevel, ToolCategory

_retriever = None


def _get_retriever():
    """惰性获取知识库检索器单例。"""
    global _retriever
    if _retriever is None:
        from knowledge.retriever import KnowledgeRetriever

        _retriever = KnowledgeRetriever()
    return _retriever


@ToolRegistry.register(
    category=ToolCategory.KNOWLEDGE,
    permission=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
)
def list_knowledge_types() -> str:
    """列出已构建的知识库类型。"""
    types = _get_retriever().list_types()
    return json.dumps({"types": types}, ensure_ascii=False)


__all__ = ["list_knowledge_types"]
