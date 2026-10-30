"""节点（意图识别）业务代码：LLM 分类面试题意图"""

from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from config.setting import get_settings
from llm.client import LLMClient
from prompts.intent import INTENT_SYSTEM_PROMPT

settings = get_settings()


class IntentResult(BaseModel):
    """意图识别结果（约束 LLM 输出结构）"""

    intent: Literal["技术面", "行为面", "案例面", "通用"] = Field(description="意图类型")
    confidence: float = Field(description="置信度 0~1")


INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", INTENT_SYSTEM_PROMPT),
    ("human", "面试题：\n{question}"),
])


def recognize_intent(question: str, llm_client: LLMClient = None) -> dict:
    """LLM 分类面试题意图，返回 { intent, intent_confidence }"""
    if llm_client is None:
        llm_client = LLMClient(
            model_name=f"{settings.model_provider}:{settings.main_model}",
            temperature=0.0,  # 分类用低温，提升稳定性
        )
    llm = llm_client.get_llm()
    structured_llm = llm.with_structured_output(IntentResult)
    chain = INTENT_PROMPT | structured_llm
    result = chain.invoke({"question": question})
    return {"intent": result.intent, "intent_confidence": result.confidence}
