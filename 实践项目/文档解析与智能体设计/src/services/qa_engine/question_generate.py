"""节点（问题生成）业务代码：面试官基于简历 + 出题知识生成三类面试问题"""

from typing import List

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from config.setting import get_settings
from llm.client import LLMClient
from prompts.question_generate import QUESTION_GENERATE_PROMPT
from services.qa_engine.skill import DOMAIN_INTERVIEW, load_domain_skills
from services.qa_engine.retrieval import flatten_fields

settings = get_settings()


class Question(BaseModel):
    """单条面试问题"""

    id: str = Field(description="问题 ID，如 q1")
    question: str = Field(description="问题内容")
    difficulty: str = Field(description="难度标签：初/中/高/专家")
    references: List[str] = Field(default_factory=list, description="关联的简历字段定位，如 experience[0]")


class QuestionList(BaseModel):
    """三类面试问题（技术/行为/案例）"""

    technical: List[Question] = Field(default_factory=list, description="技术面问题")
    behavioral: List[Question] = Field(default_factory=list, description="行为面问题")
    case: List[Question] = Field(default_factory=list, description="案例面问题")


def generate_questions(
    fields: dict,
    jd: str,
    difficulty_profile: dict,
    llm_client: LLMClient = None,
) -> dict:
    """生成三类面试问题，返回 { question_list }"""
    resume_text = _format_resume(fields)
    knowledge = load_domain_skills(DOMAIN_INTERVIEW)  # 确定性加载全部面试官出题知识

    if llm_client is None:
        llm_client = LLMClient(
            model_name=f"{settings.model_provider}:{settings.main_model}",
            temperature=0.0,  # 结构化输出用低温，提升稳定性
        )
    llm = llm_client.get_llm()
    structured_llm = llm.with_structured_output(QuestionList)

    human = (
        f"出题知识参考：\n{knowledge}\n\n"
        f"简历：\n{resume_text}\n\n"
        f"岗位JD：{jd or '未提供，基于简历生成通用问题'}\n\n"
        f"难度画像：{_format_profile(difficulty_profile)}"
    )
    result = structured_llm.invoke([
        SystemMessage(content=QUESTION_GENERATE_PROMPT),
        HumanMessage(content=human),
    ])

    return {"question_list": result.model_dump()}


def _format_resume(fields: dict) -> str:
    """把简历结构化字段格式化为「[field] text」列表"""
    lines = []
    for item in flatten_fields(fields):
        lines.append(f"- [{item['field']}] {item['text']}")
    return "\n".join(lines)


def _format_profile(profile: dict) -> str:
    """把难度画像格式化为可读文本"""
    if not profile:
        return "默认中级"
    ratio = profile.get("ratio") or {}
    return f"标签：{profile.get('tag')}；深度：{profile.get('depth')}；配比：{ratio}"
