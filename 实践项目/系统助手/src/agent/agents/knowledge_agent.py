"""KnowledgeAgent — 本地知识库问答。"""

from __future__ import annotations

from typing import Any

from agent.base_worker import BaseWorkerAgent
from agent.prompts.knowledge_prompt import KNOWLEDGE_AGENT_PROMPT
from utils.constants import ToolCategory


class KnowledgeAgent(BaseWorkerAgent):
    """知识库问答 Worker，绑定知识库检索工具。"""

    def __init__(self, provider, config: Any = None) -> None:
        super().__init__(
            provider,
            category=ToolCategory.KNOWLEDGE,
            system_prompt=KNOWLEDGE_AGENT_PROMPT,
            config=config,
        )


__all__ = ["KnowledgeAgent"]
