"""知识库检索器。

基于 PGVector 对已构建的知识库进行相似检索，支持指定类型或全类型检索，
返回带来源元数据的 ``Document`` 列表。
"""

from __future__ import annotations

from typing import Any, List, Optional

from langchain_core.documents import Document
from loguru import logger

from infrastructure.llm.embedding_provider import EmbeddingProvider
from infrastructure.postgres.pg_config import PostgresConfig
from knowledge import vector_store


class KnowledgeRetriever:
    """知识库检索器。"""

    def __init__(self, config: Any = None) -> None:
        self.config = config
        self.pg_config = PostgresConfig().load()
        self.embedding_provider = EmbeddingProvider(config)
        self.collection_prefix = self._get_str("knowledge.collection_prefix", "rag_knowledge")

    # ------------------------------------------------------------------
    def _get_str(self, key: str, default: str) -> str:
        if self.config is None:
            return default
        value = self.config.get(key, default)
        return str(value) if value is not None else default

    # ------------------------------------------------------------------
    def list_types(self) -> List[str]:
        """列出已构建的知识库类型（即已存在的 collection）。"""
        import psycopg

        prefix = f"{self.collection_prefix}_%"
        try:
            with psycopg.connect(
                host=self.pg_config.host,
                port=self.pg_config.port,
                user=self.pg_config.user,
                password=self.pg_config.password,
                dbname=self.pg_config.database,
                connect_timeout=5,
            ) as conn:
                rows = conn.execute(
                    "SELECT name FROM langchain_pg_collection "
                    "WHERE name LIKE %s ORDER BY name;",
                    (prefix,),
                ).fetchall()
        except Exception as exc:  # noqa: BLE001 - 检索前降级为空列表
            logger.warning(f"查询知识库类型失败: {exc}")
            return []

        prefix_len = len(self.collection_prefix) + 1
        return [name[prefix_len:] for (name,) in rows]

    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        doc_type: Optional[str] = None,
        k: int = 4,
    ) -> List[Document]:
        """相似检索。

        Args:
            query: 用户问题或检索关键词。
            doc_type: 知识库类型；为 None 时检索全部已构建类型。
            k: 每个类型返回的文档数量。

        Returns:
            命中的 Document 列表（含 ``source`` 等元数据）。
        """
        if doc_type:
            return self._search_one(query, doc_type, k)

        results: List[Document] = []
        for doc_type in self.list_types():
            results.extend(self._search_one(query, doc_type, k))
        return results

    # ------------------------------------------------------------------
    def _search_one(self, query: str, doc_type: str, k: int) -> List[Document]:
        try:
            store = vector_store.create_vector_store(
                self.embedding_provider.get_embeddings(),
                self.pg_config.build_uri(),
                doc_type,
                collection_prefix=self.collection_prefix,
            )
            return store.similarity_search(query, k=k)
        except Exception as exc:  # noqa: BLE001 - 单类型失败不阻断其余类型
            logger.warning(f"检索类型 [{doc_type}] 失败: {exc}")
            return []


__all__ = ["KnowledgeRetriever"]
