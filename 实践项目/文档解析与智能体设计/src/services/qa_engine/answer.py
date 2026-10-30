"""节点（回答生成）业务代码：agent 以候选人身份，结合简历 + SKILL 知识生成参考答案"""

from typing import List

from langchain.agents import create_agent

from config.setting import get_settings
from llm.client import LLMClient
from prompts.answer import ANSWER_SYSTEM_PROMPT
from services.qa_engine.skill import SkillMiddleware, DOMAIN_COACHING

settings = get_settings()


def generate_answer(
    question: str,
    intent: str,
    retrieved: list,
    llm_client: LLMClient = None,
) -> dict:
    """结合简历与 SKILL 知识生成参考答案，返回 { answer, citations }"""
    resume_text = _format_retrieved(retrieved)

    if llm_client is None:
        llm_client = LLMClient(
            model_name=f"{settings.model_provider}:{settings.main_model}",
            temperature=0.0,  # 工具调用需稳定，低温降低乱码概率
        )
    llm = llm_client.get_llm()

    # 工具调用生成回答（SkillMiddleware 负责渐进式披露 + 暴露 load_skill 工具）
    agent = create_agent(
        model=llm,
        middleware=[SkillMiddleware(domain=DOMAIN_COACHING)],
        system_prompt=ANSWER_SYSTEM_PROMPT,
    )
    human = f"面试题：{question}\n问题意图：{intent}\n\n简历片段：\n{resume_text}"
    result = agent.invoke({"messages": [("user", human)]})
    answer = result["messages"][-1].content

    return {"answer": answer, "citations": _extract_citations(answer, retrieved)}


def _format_retrieved(retrieved: list) -> str:
    """把简历检索块格式化为「[field] text」列表（知识块已改由 load_skill 按需加载）"""
    lines = []
    for item in retrieved:
        if item.get("source") == "resume":
            lines.append(f"- [{item['field']}] {item['text']}")
    return "\n".join(lines)


def _extract_citations(answer: str, retrieved: list) -> List[str]:
    """确定性抽取：简历字段的具体值出现在回答中才算引用（宁缺毋滥）"""
    citations = []
    for item in retrieved:
        if item.get("source") != "resume":
            continue
        if _chunk_referenced(item.get("text", ""), answer):
            citations.append(item["field"])
    return citations


def _chunk_referenced(chunk_text: str, answer: str) -> bool:
    """判断回答是否出现了该简历块的某个具体值"""
    for value in _extract_values(chunk_text):
        if len(value) >= 2 and value in answer:
            return True
    return False


def _extract_values(chunk_text: str) -> List[str]:
    """从 'key: value; key: value' 提取所有 value；无 key 前缀的纯文本整体作为一个 value"""
    if ": " not in chunk_text:
        return [chunk_text.strip()] if chunk_text.strip() else []
    values = []
    for part in chunk_text.split("; "):
        if ": " in part:
            values.append(part.split(": ", 1)[1].strip())
    return values
