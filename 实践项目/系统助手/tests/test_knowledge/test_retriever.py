"""知识库检索器单元测试。"""

from __future__ import annotations

from langchain_core.documents import Document

import knowledge.retriever as retriever_module
from knowledge.retriever import KnowledgeRetriever


class _FakePgConfig:
    host = "127.0.0.1"
    port = 5432
    user = "postgres"
    password = "root"
    database = "dbvector"

    def load(self):
        return self

    def build_uri(self):
        return "postgresql+psycopg://postgres:root@127.0.0.1:5432/dbvector"


class _FakeEmbeddingProvider:
    def __init__(self, config=None):
        pass

    def get_embeddings(self, model_name=None):
        return object()


def _make_retriever(monkeypatch):
    monkeypatch.setattr(retriever_module, "PostgresConfig", _FakePgConfig)
    monkeypatch.setattr(retriever_module, "EmbeddingProvider", _FakeEmbeddingProvider)
    return KnowledgeRetriever()


class _FakeRows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        return _FakeRows(self._rows)


def test_list_types(monkeypatch):
    """list_types 将 collection 名解析为类型名。"""
    monkeypatch.setattr(
        "psycopg.connect",
        lambda **kwargs: _FakeConn([("rag_knowledge_技术文档",), ("rag_knowledge_faq",)]),
    )
    retriever = _make_retriever(monkeypatch)
    assert retriever.list_types() == ["技术文档", "faq"]


def test_search_specific_type(monkeypatch):
    """指定类型时仅检索该类型一次。"""
    calls = []

    class _FakeStore:
        def similarity_search(self, query, k=4):
            calls.append(query)
            return [Document(page_content="命中", metadata={"source": "s"})]

    monkeypatch.setattr(
        retriever_module.vector_store,
        "create_vector_store",
        lambda *args, **kwargs: _FakeStore(),
    )
    retriever = _make_retriever(monkeypatch)
    docs = retriever.search("问题", doc_type="技术文档", k=2)
    assert len(docs) == 1
    assert len(calls) == 1


def test_search_all_types(monkeypatch):
    """未指定类型时检索全部已构建类型。"""
    monkeypatch.setattr(KnowledgeRetriever, "list_types", lambda self: ["a", "b"])

    class _FakeStore:
        def similarity_search(self, query, k=4):
            return [Document(page_content="x")]

    monkeypatch.setattr(
        retriever_module.vector_store,
        "create_vector_store",
        lambda *args, **kwargs: _FakeStore(),
    )
    retriever = _make_retriever(monkeypatch)
    docs = retriever.search("问题", doc_type=None, k=2)
    assert len(docs) == 2


def test_search_returns_empty_on_error(monkeypatch):
    """单类型检索异常时返回空列表，不抛出。"""
    monkeypatch.setattr(KnowledgeRetriever, "list_types", lambda self: ["a"])

    def _boom(*args, **kwargs):
        raise RuntimeError("store error")

    monkeypatch.setattr(retriever_module.vector_store, "create_vector_store", _boom)
    retriever = _make_retriever(monkeypatch)
    assert retriever.search("问题", doc_type="a") == []
