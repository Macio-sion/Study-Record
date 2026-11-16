"""PGVector 向量库构建与索引管理。

基于 ``langchain_postgres.PGVector`` 为每个知识库类型创建独立的向量表，
固定向量维度（默认 4096），并提供 HNSW 索引创建能力。
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy
from loguru import logger

from infrastructure.postgres.pg_config import PostgresConfig


def build_collection_name(prefix: str, doc_type: str) -> str:
    """生成向量表名，形如 ``rag_knowledge_{type}``。"""
    return f"{prefix}_{doc_type}"


def create_vector_store(
    embeddings: Embeddings,
    connection_uri: str,
    doc_type: str,
    collection_prefix: str = "rag_knowledge",
    embedding_length: int = 4096,
    pre_delete_collection: bool = False,
) -> PGVector:
    """创建（或复用）指定类型的 PGVector 向量库。

    ``embedding_length`` 用于固定向量维度；PGVector 会在首次写入时自动建表，
    若 ``pre_delete_collection`` 为 True 则先删除同名表再重建。
    """
    collection_name = build_collection_name(collection_prefix, doc_type)
    return PGVector(
        embeddings=embeddings,
        connection=connection_uri,
        collection_name=collection_name,
        embedding_length=embedding_length,
        distance_strategy=DistanceStrategy.COSINE,
        use_jsonb=True,
        pre_delete_collection=pre_delete_collection,
    )


def create_hnsw_index(pg_config: PostgresConfig, vector_dim: int = 4096) -> bool:
    """尝试为向量嵌入表创建 HNSW 索引（余弦距离），失败时降级为顺序扫描。

    说明：pgvector 的 HNSW 索引对 ``vector`` 类型最多支持 2000 维（``halfvec``
    4000 维）。当嵌入维度（如 qwen3-embedding 的 4096 维）超过该上限时，索引
    无法创建，此时仅记录告警并降级为顺序扫描，不影响知识库的构建与检索功能。
    """
    import psycopg

    try:
        with psycopg.connect(
            host=pg_config.host,
            port=pg_config.port,
            user=pg_config.user,
            password=pg_config.password,
            dbname=pg_config.database,
            connect_timeout=10,
        ) as conn:
            # 明确向量列维度（满足 vector(N) 需求），已为同类型时忽略
            try:
                conn.execute(
                    f"ALTER TABLE langchain_pg_embedding "
                    f"ALTER COLUMN embedding TYPE vector({vector_dim});"
                )
            except Exception:  # noqa: BLE001 - 已为同维度时回滚忽略
                conn.rollback()
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_hnsw "
                "ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops);"
            )
            conn.commit()
        logger.info("HNSW 索引已就绪")
        return True
    except Exception as exc:  # noqa: BLE001 - 维度超限等，降级为顺序扫描
        logger.warning(f"HNSW 索引创建失败，降级为顺序扫描: {exc}")
        return False


__all__ = ["build_collection_name", "create_vector_store", "create_hnsw_index"]
