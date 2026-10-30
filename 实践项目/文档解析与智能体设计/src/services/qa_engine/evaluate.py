"""节点（追问评估）业务代码：面试官点评/评分/追问"""

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from config.setting import get_settings
from llm.client import LLMClient
from prompts.evaluate import EVALUATE_PROMPT

settings = get_settings()


class Feedback(BaseModel):
    """追问评估结果"""

    score: int = Field(description="评分 0-100")
    comment: str = Field(description="点评")
    follow_up: str = Field(default="", description="追问内容（可选，无追问为空）")


def evaluate_answer(
    question: str,
    user_answer: str,
    llm_client: LLMClient = None,
) -> dict:
    """点评/评分/追问用户回答，返回 { feedback }"""
    if llm_client is None:
        llm_client = LLMClient(
            model_name=f"{settings.model_provider}:{settings.main_model}",
            temperature=0.0,  # 结构化输出用低温，提升稳定性
        )
    llm = llm_client.get_llm()
    structured_llm = llm.with_structured_output(Feedback)

    human = f"面试题：{question}\n候选人回答：{user_answer}"
    result = structured_llm.invoke([
        SystemMessage(content=EVALUATE_PROMPT),
        HumanMessage(content=human),
    ])

    return {"feedback": result.model_dump()}
