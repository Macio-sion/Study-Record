"""知识库检索工具。"""

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
def search_knowledge(query: str, doc_type: str = "", k: int = 4) -> str:
    """在本地知识库中检索与问题相关的内容。

    Args:
        query: 用户问题或检索关键词。
        doc_type: 知识库类型（留空则检索全部已构建类型）。
        k: 返回的文档数量。
    """
    docs = _get_retriever().search(query, doc_type or None, k)
    if not docs:
        return json.dumps(
            {"found": False, "message": "知识库中未找到相关内容"},
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "found": True,
            "count": len(docs),
            "results": [
                {"content": d.page_content, "source": d.metadata.get("source", "")}
                for d in docs
            ],
        },
        ensure_ascii=False,
    )


__all__ = ["search_knowledge"]
