"""本地嵌入模型 Provider。

封装 Ollama 嵌入模型的加载，默认使用 ``qwen3-embedding``（向量维度 4096）。
与 ``OllamaProvider`` 共享相同的 ``base_url`` 配置，纯本地离线。
"""

from __future__ import annotations

from typing import Any, Optional

from langchain_ollama import OllamaEmbeddings


class EmbeddingProvider:
    """本地嵌入模型提供者（Ollama）。"""

    def __init__(self, config: Any = None) -> None:
        """初始化嵌入模型提供者。

        Args:
            config: 完整 ``ConfigManager`` 实例；从中读取 ``llm.ollama.base_url``
                与 ``knowledge.embedding_model``，读取失败时回退默认值。
        """
        self.base_url: str = "http://127.0.0.1:11434"
        self.model: str = "qwen3-embedding"
        if config is not None:
            try:
                self.base_url = str(config.llm.ollama.base_url or self.base_url)
            except AttributeError:
                pass
            try:
                self.model = str(config.knowledge.embedding_model or self.model)
            except AttributeError:
                pass

    # ------------------------------------------------------------------
    def get_embeddings(self, model_name: Optional[str] = None) -> OllamaEmbeddings:
        """获取 ``OllamaEmbeddings`` 实例。"""
        return OllamaEmbeddings(model=model_name or self.model, base_url=self.base_url)


__all__ = ["EmbeddingProvider"]
