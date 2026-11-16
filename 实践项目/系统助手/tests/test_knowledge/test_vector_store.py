"""向量库构建单元测试。"""

from __future__ import annotations

import knowledge.vector_store as vector_store_module
from knowledge.vector_store import build_collection_name, create_vector_store


def test_build_collection_name():
    """表名由前缀与类型拼接。"""
    assert build_collection_name("rag_knowledge", "技术文档") == "rag_knowledge_技术文档"
    assert build_collection_name("rag_knowledge", "faq") == "rag_knowledge_faq"


def test_create_vector_store_params(monkeypatch):
    """create_vector_store 透传正确的 collection_name 与维度。"""
    captured = {}

    class _FakePGVector:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(vector_store_module, "PGVector", _FakePGVector)

    create_vector_store(
        embeddings=object(),
        connection_uri="postgresql+psycopg://x",
        doc_type="技术文档",
        collection_prefix="rag_knowledge",
        embedding_length=4096,
        pre_delete_collection=True,
    )
    assert captured["collection_name"] == "rag_knowledge_技术文档"
    assert captured["embedding_length"] == 4096
    assert captured["pre_delete_collection"] is True


def test_create_hnsw_index_success(monkeypatch):
    """HNSW 索引创建成功返回 True。"""
    executed = []

    class _FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql):
            executed.append(sql)

        def commit(self):
            return None

        def rollback(self):
            return None

    monkeypatch.setattr("psycopg.connect", lambda **kwargs: _FakeConn())

    class _PgConfig:
        host = "127.0.0.1"
        port = 5432
        user = "postgres"
        password = "root"
        database = "dbvector"

    ok = vector_store_module.create_hnsw_index(_PgConfig(), 4096)
    assert ok is True
    assert any("hnsw" in sql for sql in executed)


def test_create_hnsw_index_failure(monkeypatch):
    """维度超限等异常时降级返回 False，不抛出。"""

    def _raise(**kwargs):
        raise RuntimeError("column cannot have more than 2000 dimensions")

    monkeypatch.setattr("psycopg.connect", _raise)

    class _PgConfig:
        host = "127.0.0.1"
        port = 5432
        user = "postgres"
        password = "root"
        database = "dbvector"

    assert vector_store_module.create_hnsw_index(_PgConfig(), 4096) is False
