"""节点（总结报告）业务代码：确定性计算评分 + LLM 生成亮点/建议"""

from typing import List, Tuple

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from config.setting import get_settings
from llm.client import LLMClient
from prompts.summarize import SUMMARIZE_PROMPT

settings = get_settings()

_DIMENSION_KEYS = ("technical", "behavioral", "case")


class ReportSummary(BaseModel):
    """亮点与建议（定性部分，LLM 生成）"""

    highlights: List[str] = Field(default_factory=list, description="候选人的亮点")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")


def summarize_report(qa_records: list, llm_client: LLMClient = None) -> dict:
    """生成评估报告：确定性计算总分/分维度，LLM 生成亮点/建议"""
    total_score, dimensions = _calc_scores(qa_records)
    highlights, suggestions = _gen_qualitative(qa_records, llm_client)
    return {
        "total_score": total_score,
        "dimensions": dimensions,
        "highlights": highlights,
        "suggestions": suggestions,
    }


def _calc_scores(qa_records: list) -> Tuple[int, dict]:
    """确定性：总分 = 各题均分；维度 = 各分类均分"""
    scores = [r.get("score", 0) for r in qa_records]
    total = round(sum(scores) / len(scores)) if scores else 0

    dimensions = {}
    for cat in _DIMENSION_KEYS:
        cat_scores = [r.get("score", 0) for r in qa_records if r.get("category") == cat]
        if cat_scores:
            dimensions[cat] = round(sum(cat_scores) / len(cat_scores))
    return total, dimensions


def _gen_qualitative(qa_records: list, llm_client: LLMClient = None) -> Tuple[List[str], List[str]]:
    """LLM 生成亮点与建议"""
    if llm_client is None:
        llm_client = LLMClient(
            model_name=f"{settings.model_provider}:{settings.main_model}",
            temperature=0.0,  # 结构化输出用低温
        )
    llm = llm_client.get_llm()
    structured_llm = llm.with_structured_output(ReportSummary)

    human = _format_records(qa_records)
    result = structured_llm.invoke([
        SystemMessage(content=SUMMARIZE_PROMPT),
        HumanMessage(content=human),
    ])
    return result.highlights, result.suggestions


def _format_records(qa_records: list) -> str:
    """把问答记录格式化为可读文本"""
    lines = []
    for i, r in enumerate(qa_records, 1):
        cat = r.get("category", "")
        lines.append(
            f"{i}. [{cat}] 问题：{r.get('question')}（得分 {r.get('score')}）\n"
            f"   回答：{r.get('answer')}"
        )
    return "\n\n".join(lines)
