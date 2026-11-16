"""ChromaDB 向量存储封装（可选，可后置）。

为「工具描述向量化 / 语义检索」提供统一接口。依赖 ``langchain-chroma`` +
``chromadb``，采用惰性导入：未安装时模块可正常 import，仅在调用相关方法时
才提示缺少依赖。

> 当前阶段工具选择使用「按分类绑定」策略，本模块作为可扩展能力预留，未接入主流程。
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple


class ChromaStore:
    """ChromaDB 向量存储封装。"""

    def __init__(self, collection_name: str = "system_assistant", persist_dir: Optional[str] = None) -> None:
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self._vectorstore = None

    # ------------------------------------------------------------------
    def _ensure_store(self):
        """惰性加载 Chroma，未安装依赖时抛出可读错误。"""
        if self._vectorstore is not None:
            return self._vectorstore
        try:
            from langchain_chroma import Chroma
            from langchain_ollama import OllamaEmbeddings
        except ImportError as exc:  # pragma: no cover - 依赖可选
            raise ImportError(
                "ChromaDB 向量存储依赖未安装，请执行: pip install langchain-chroma chromadb"
            ) from exc

        embeddings = OllamaEmbeddings(model="qwen2.5:7b-instruct-q4_K_M")
        kwargs: dict = {"collection_name": self.collection_name, "embedding_function": embeddings}
        if self.persist_dir:
            kwargs["persist_directory"] = self.persist_dir

        self._vectorstore = Chroma(**kwargs)
        return self._vectorstore

    # ------------------------------------------------------------------
    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[str]:
        """向量化并写入一批文本，返回 id 列表。"""
        store = self._ensure_store()
        return store.add_texts(texts, metadatas=metadatas)

    def similarity_search(self, query: str, k: int = 4) -> List[Any]:
        """语义相似检索，返回 top-k 文档。"""
        store = self._ensure_store()
        return store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Any, float]]:
        """语义相似检索（带距离分数）。"""
        store = self._ensure_store()
        return store.similarity_search_with_score(query, k=k)


__all__ = ["ChromaStore"]