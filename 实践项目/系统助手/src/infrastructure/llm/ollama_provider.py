"""Ollama 本地 LLM Provider。

封装 Ollama 的连接检测、模型列表获取、ChatOllama 实例创建与 GPU 显存释放。
纯本地离线，默认不调用任何网络 API。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, List, Optional

from langchain_ollama import ChatOllama
from loguru import logger


class OllamaProvider:
    """Ollama 本地 LLM 提供者。"""

    def __init__(self, config: Any) -> None:
        """config 为 ``llm`` 配置节点（含 ollama 子节点）。"""
        ollama_cfg = config.ollama
        self.base_url: str = ollama_cfg.base_url or "http://127.0.0.1:11434"
        self.current_model: str = ollama_cfg.model or "qwen2.5:7b-instruct-q4_K_M"
        self.lightweight_model: str = getattr(ollama_cfg, "lightweight_model", "qwen3.5:0.8b")
        self.idle_timeout: int = int(getattr(ollama_cfg, "idle_timeout", 30))
        self.temperature: float = float(getattr(ollama_cfg, "temperature", 0.1))

    # ------------------------------------------------------------------
    def get_chat_model(self, model_name: Optional[str] = None) -> ChatOllama:
        """获取 LangChain ChatOllama 实例。"""
        model = model_name or self.current_model
        return ChatOllama(
            model=model,
            base_url=self.base_url,
            temperature=self.temperature,
        )

    # ------------------------------------------------------------------
    def _request(self, path: str, method: str = "GET", data: Optional[dict] = None, timeout: int = 3):
        """发起 HTTP 请求到 Ollama 服务。"""
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def is_available(self) -> bool:
        """检测 Ollama 服务是否可用。"""
        try:
            self._request("/api/tags", timeout=2)
            return True
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def list_models(self) -> List[str]:
        """列出本地可用模型。"""
        try:
            resp = self._request("/api/tags")
            models = resp.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
        except (urllib.error.URLError, OSError, ValueError) as exc:
            logger.warning(f"获取 Ollama 模型列表失败: {exc}")
            return []

    def release_gpu(self) -> None:
        """释放 GPU 显存 (keep_alive=0)，模型文件保留在磁盘。"""
        try:
            self._request(
                "/api/generate",
                method="POST",
                data={"model": self.current_model, "keep_alive": 0},
                timeout=5,
            )
            logger.info(f"GPU 显存已释放 (模型: {self.current_model}，文件保留)")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            logger.warning(f"释放 GPU 显存失败: {exc}")


__all__ = ["OllamaProvider"]