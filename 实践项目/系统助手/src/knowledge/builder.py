"""知识库构建入口。

串联「文档加载 → 数据清洗 → 文本切分 → 向量库构建 → 入库」，支持按类型
构建与重建。构建结果以字典返回，便于上层 Agent / 工具 JSON 序列化。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from infrastructure.llm.embedding_provider import EmbeddingProvider
from infrastructure.postgres.pg_config import PostgresConfig
from knowledge import cleaners, loaders, splitter, vector_store

# 项目根目录：knowledge -> src -> 项目根
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeBuilder:
    """知识库构建器。"""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.pg_config = PostgresConfig().load()
        self.embedding_provider = EmbeddingProvider(config)
        self.knowledge_dir = _PROJECT_ROOT / self._get_str("knowledge.knowledge_dir", "knowledge")
        self.collection_prefix = self._get_str("knowledge.collection_prefix", "rag_knowledge")
        self.chunk_size = self._get_int("knowledge.chunk_size", 1024)
        self.chunk_overlap = self._get_int("knowledge.chunk_overlap", 256)
        self.chunk_min_size = self._get_int("knowledge.chunk_min_size", 256)
        self.vector_dim = self._get_int("knowledge.vector_dim", 4096)

    # ------------------------------------------------------------------
    def _get_str(self, key: str, default: str) -> str:
        value = self.config.get(key, default)
        return str(value) if value is not None else default

    def _get_int(self, key: str, default: int) -> int:
        try:
            return int(self.config.get(key, default))
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------------
    def list_types(self) -> List[str]:
        """列出当前可用的知识库类型。"""
        return loaders.list_knowledge_types(self.knowledge_dir)

    # ------------------------------------------------------------------
    def build(self, doc_type: str, rebuild: bool = False) -> Dict[str, Any]:
        """构建指定类型的知识库。

        Args:
            doc_type: 文档类型（对应 ``/knowledge/{doc_type}/`` 子目录）。
            rebuild: 是否先删除同名向量表再重建。

        Returns:
            含 ``success``、``doc_type``、``chunk_count``、``collection`` 的结果字典。
        """
        documents = loaders.load_pdf_documents(self.knowledge_dir, doc_type)
        documents = cleaners.clean_documents(documents)
        chunks = splitter.split_documents(
            documents,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            min_chunk_size=self.chunk_min_size,
        )
        if not chunks:
            logger.warning(f"知识库类型 [{doc_type}] 无有效文档块")
            return {
                "success": False,
                "doc_type": doc_type,
                "chunk_count": 0,
                "message": f"未在 {self.knowledge_dir / doc_type} 找到有效文档",
            }

        embeddings = self.embedding_provider.get_embeddings()
        connection_uri = self.pg_config.build_uri()
        store = vector_store.create_vector_store(
            embeddings,
            connection_uri,
            doc_type,
            collection_prefix=self.collection_prefix,
            embedding_length=self.vector_dim,
            pre_delete_collection=rebuild,
        )
        ids = store.add_documents(chunks)
        collection_name = vector_store.build_collection_name(self.collection_prefix, doc_type)
        vector_store.create_hnsw_index(self.pg_config, self.vector_dim)

        logger.info(f"知识库 [{doc_type}] 构建完成，入库 {len(ids)} 个块")
        return {
            "success": True,
            "doc_type": doc_type,
            "chunk_count": len(ids),
            "collection": collection_name,
        }


__all__ = ["KnowledgeBuilder"]
