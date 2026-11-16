"""知识库工具组单元测试。"""

from __future__ import annotations

import importlib
import json

from langchain_core.documents import Document

# 用 import_module 获取真实子模块，避免与包 __init__ 导出的同名函数冲突
sk_module = importlib.import_module("tools.knowledge.search_knowledge")
lkt_module = importlib.import_module("tools.knowledge.list_knowledge_types")


def test_search_knowledge_found(monkeypatch):
    """检索命中时返回 found=True 与结果。"""
    class _FakeRetriever:
        def search(self, query, doc_type=None, k=4):
            return [Document(page_content="命中内容", metadata={"source": "s.pdf"})]

    monkeypatch.setattr(sk_module, "_retriever", _FakeRetriever())
    data = json.loads(sk_module.search_knowledge("问题"))
    assert data["found"] is True
    assert data["count"] == 1
    assert data["results"][0]["content"] == "命中内容"


def test_search_knowledge_empty(monkeypatch):
    """检索无命中时返回 found=False。"""
    class _FakeRetriever:
        def search(self, query, doc_type=None, k=4):
            return []

    monkeypatch.setattr(sk_module, "_retriever", _FakeRetriever())
    data = json.loads(sk_module.search_knowledge("问题"))
    assert data["found"] is False


def test_search_knowledge_passes_doc_type(monkeypatch):
    """doc_type 参数正确传递给检索器。"""
    class _FakeRetriever:
        def __init__(self):
            self.calls = []

        def search(self, query, doc_type=None, k=4):
            self.calls.append((query, doc_type, k))
            return [Document(page_content="x")]

    retriever = _FakeRetriever()
    monkeypatch.setattr(sk_module, "_retriever", retriever)
    sk_module.search_knowledge("问题", doc_type="技术文档", k=3)
    assert retriever.calls == [("问题", "技术文档", 3)]


def test_list_knowledge_types(monkeypatch):
    """列出知识库类型。"""
    class _FakeRetriever:
        def list_types(self):
            return ["技术文档", "faq"]

    monkeypatch.setattr(lkt_module, "_retriever", _FakeRetriever())
    data = json.loads(lkt_module.list_knowledge_types())
    assert data["types"] == ["技术文档", "faq"]
