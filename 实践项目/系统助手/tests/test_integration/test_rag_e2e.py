"""RAG 端到端集成测试（构建 → 检索）。

依赖真实 Postgres 与 Ollama 嵌入模型，任一不可用时自动跳过。
覆盖「向量入库 → 相似检索」的确定性链路；LLM 生成问答留待 UI 冒烟测试。
"""

from __future__ import annotations

import pytest
from langchain_core.documents import Document


def _services_available() -> bool:
    """检测 Postgres 与 Ollama 是否可用。"""
    try:
        import urllib.request

        import psycopg
        from infrastructure.postgres.pg_config import PostgresConfig

        pg = PostgresConfig().load()
        with psycopg.connect(
            host=pg.host,
            port=pg.port,
            user=pg.user,
            password=pg.password,
            dbname=pg.database,
            connect_timeout=3,
        ) as conn:
            conn.execute("SELECT 1")
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
        return True
    except Exception:  # noqa: BLE001 - 任一服务不可用即跳过
        return False


@pytest.mark.skipif(not _services_available(), reason="Postgres 或 Ollama 不可用")
def test_build_and_retrieve():
    """真实链路：向量入库后，检索返回语义匹配的内容。"""
    from infrastructure.config.config_manager import ConfigManager
    from infrastructure.llm.embedding_provider import EmbeddingProvider
    from infrastructure.postgres.pg_config import PostgresConfig
    from knowledge import vector_store
    from knowledge.retriever import KnowledgeRetriever

    cm = ConfigManager().load()
    pg = PostgresConfig().load()
    embeddings = EmbeddingProvider(cm).get_embeddings()

    store = vector_store.create_vector_store(
        embeddings,
        pg.build_uri(),
        "_it_test",
        collection_prefix="rag_knowledge",
        embedding_length=4096,
        pre_delete_collection=True,
    )
    store.add_documents([
        Document(page_content="Python 是一种解释型编程语言", metadata={"type": "it"}),
        Document(page_content="报销流程需要提交发票", metadata={"type": "it"}),
    ])

    retriever = KnowledgeRetriever(cm)
    docs = retriever.search("编程语言", doc_type="_it_test", k=1)

    assert docs, "检索应返回结果"
    assert "Python" in docs[0].page_content

    store.delete_collection()
