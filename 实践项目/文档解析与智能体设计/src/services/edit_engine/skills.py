"""简历生成与优化 SKILL 库：简历生成 + 8 类优化 SKILL

每条优化建议执行 ReAct 循环（分析 → 生成 → 校验），保证建议可追溯（原文 → 优化后）。
- 分析（analyze）：确定性抽取简历统计 + JD 关键词，作为生成上下文
- 生成（generate）：LLM 结构化输出 EditSuggestion[]
- 校验（validate）：确定性过滤无实质改动 / 空建议，并回填唯一 ID
"""

import re
from typing import List, Literal

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from config.setting import get_settings
from llm.client import LLMClient
from prompts.edit import GENERATE_RESUME_SYSTEM_PROMPT, OPTIMIZE_SYSTEM_PROMPT
from services.document_processing_engine.structure_extract import StructuredResume
from services.qa_engine.retrieval import flatten_fields

settings = get_settings()

# 优化类型 -> (SKILL 名, 优化规则说明)
SKILL_TYPES = {
    "star": ("STAR", "检测经历描述的 STAR 四要素（情境 Situation/任务 Task/行动 Action/结果 Result），补全缺失要素"),
    "quantify": ("QUANTIFY", "将模糊成果量化（直接量化/相对量化/行业基准），把「提升了效率」改写为「效率提升 40%」"),
    "keyword": ("KEYWORD", "基于 JD 关键词做覆盖对比，把简历中缺失的关键词补充进对应经历/技能"),
    "verb": ("VERB", "将被动词替换为主动动词（如「负责」「参与」改写为「主导」「搭建」「推动」）"),
    "layout": ("LAYOUT", "字体/行距/层级/留白排版检测，给出可读性与层次感建议"),
    "ats": ("ATS", "ATS 兼容性检测（多栏/特殊字体/表格/图片文字导致机器无法解析的风险）"),
    "paragraph": ("PARAGRAPH", "分段落的表达与逻辑优化，让描述更简洁、聚焦、有冲击力"),
    "length": ("LENGTH", "篇幅诊断与删减/补充建议（单页/两页定位的详略取舍）"),
}

# 缺省执行全部优化类型（F-EDIT-003 ~ 008, 011, 012）
ALL_OPTIMIZE_TYPES = list(SKILL_TYPES.keys())

# 停用词（JD 关键词提取用）
_STOPWORDS = {
    "的", "了", "和", "与", "及", "或", "在", "是", "有", "等", "对", "为", "并",
    "负责", "要求", "经验", "能力", "优先", "熟悉", "掌握", "了解", "具备", "相关",
    "以上", "工作", "岗位", "职责", "任职", "以及", "能够",
}


class SuggestionTarget(BaseModel):
    field: str = Field(description="所属简历区块定位，如 experience[0]")
    text: str = Field(description="该区块的原文块内容")


class EditSuggestion(BaseModel):
    id: str = Field(default="", description="建议 ID")
    type: str = Field(description="建议类型：STAR/QUANTIFY/KEYWORD/VERB/LAYOUT/ATS/PARAGRAPH/LENGTH")
    target: SuggestionTarget = Field(description="目标字段定位与原文块")
    before: str = Field(description="修改前内容")
    after: str = Field(description="修改后内容")
    explain: str = Field(description="优化依据说明")
    location: str = Field(description="要修改的叶子字段路径，如 experience[0].description、summary")
    priority: Literal["high", "medium", "low"] = Field(default="medium", description="优先级")


class SuggestionList(BaseModel):
    suggestions: List[EditSuggestion] = Field(default_factory=list, description="优化建议列表")


def _default_llm() -> LLMClient:
    return LLMClient(
        model_name=f"{settings.model_provider}:{settings.main_model}",
        temperature=0.0,  # 结构化输出用低温，提升稳定性
    )


def normalize_fields(fields: dict) -> dict:
    """把纯值字段规整为 {value, confidence} 结构（生成/手动输入来源置信度记为 1.0）"""
    if not isinstance(fields, dict):
        return {}
    return _normalize_node(fields)


def _normalize_node(node):
    if isinstance(node, dict):
        if "value" in node and "confidence" in node:
            return node
        if "value" in node:
            return {"value": node["value"], "confidence": node.get("confidence", 1.0)}
        return {k: _normalize_node(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_normalize_node(i) for i in node]
    return {"value": node, "confidence": 1.0}


def generate_resume(resume_data: dict, llm_client: LLMClient = None) -> dict:
    """SKILL-1 简历生成：依据输入生成整份结构化简历，返回 { generated_resume }"""
    llm_client = llm_client or _default_llm()
    llm = llm_client.get_llm()
    structured_llm = llm.with_structured_output(StructuredResume)

    source_text = _format_resume(resume_data)
    human = f"简历素材：\n{source_text or '（无现有素材，请根据用户输入生成）'}"
    result = structured_llm.invoke([
        SystemMessage(content=GENERATE_RESUME_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ])

    return {"generated_resume": normalize_fields(result.model_dump())}


def optimize_skills(
    resume_data: dict,
    jd: str = "",
    optimize_types: List[str] = None,
    llm_client: LLMClient = None,
) -> List[dict]:
    """逐条优化：按优化类型串行执行各 SKILL（ReAct 分析→生成→校验），返回 EditSuggestion[]"""
    fields = resume_data.get("fields", resume_data) if isinstance(resume_data, dict) else {}
    types = [t for t in (optimize_types or ALL_OPTIMIZE_TYPES) if t in SKILL_TYPES]

    llm_client = llm_client or _default_llm()
    llm = llm_client.get_llm()
    structured_llm = llm.with_structured_output(SuggestionList)

    # 分析（确定性）：简历统计 + JD 关键词
    resume_text = _format_resume(fields)
    analysis = _analyze_resume(fields)
    jd_keywords = _extract_jd_keywords(jd)

    suggestions: List[dict] = []
    for skill_type in types:
        name, rule = SKILL_TYPES[skill_type]
        human = _build_skill_human(skill_type, name, rule, resume_text, jd, jd_keywords, analysis)
        result = structured_llm.invoke([
            SystemMessage(content=OPTIMIZE_SYSTEM_PROMPT),
            HumanMessage(content=human),
        ])
        suggestions.extend(sug.model_dump() for sug in result.suggestions)

    # 校验（确定性）
    return _validate_suggestions(suggestions)


def _format_resume(fields: dict) -> str:
    """把简历结构化字段格式化为「[field] text」列表"""
    lines = [f"- [{item['field']}] {item['text']}" for item in flatten_fields(fields)]
    return "\n".join(lines)


def _analyze_resume(fields: dict) -> dict:
    """分析（确定性）：统计简历规模与缺失板块"""
    blocks = flatten_fields(fields)
    return {
        "total_chars": sum(len(b.get("text", "")) for b in blocks),
        "field_count": len(blocks),
        "experience_count": len(fields.get("experience") or []),
        "missing_sections": [
            k for k in ("personal", "education", "experience", "skills", "summary")
            if not fields.get(k)
        ],
    }


def _extract_jd_keywords(jd: str) -> List[str]:
    """分析（确定性）：从 JD 抽取关键词（英文/数字/技术词 + 2~4 字中文词）"""
    if not jd:
        return []
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]*|[\u4e00-\u9fff]{2,4}", jd)
    keywords, seen = [], set()
    for t in tokens:
        t = t.strip()
        if len(t) < 2 or t in _STOPWORDS or t in seen:
            continue
        seen.add(t)
        keywords.append(t)
    return keywords[:40]


def _build_skill_human(skill_type, name, rule, resume_text, jd, jd_keywords, analysis) -> str:
    lines = [
        f"优化类型：{name}（{skill_type}）",
        f"优化规则：{rule}",
        f"简历文本：\n{resume_text}",
        f"岗位 JD：{jd or '未提供（关键词/ATS 降级为通用规则）'}",
    ]
    if jd_keywords:
        lines.append(f"JD 关键词：{', '.join(jd_keywords)}")
    lines.append(
        f"简历分析：总字数 {analysis['total_chars']}，字段数 {analysis['field_count']}，"
        f"经历数 {analysis['experience_count']}，缺失板块 {analysis['missing_sections'] or '无'}"
    )
    return "\n\n".join(lines)


def _validate_suggestions(suggestions: List[dict]) -> List[dict]:
    """校验（确定性）：过滤空建议 / 无实质改动，补齐缺失定位与唯一 ID"""
    valid = []
    for i, sug in enumerate(suggestions, 1):
        before = (sug.get("before") or "").strip()
        after = (sug.get("after") or "").strip()
        if not after or after == before:
            continue
        location = (sug.get("location") or "").strip()
        if not location:
            location = (sug.get("target") or {}).get("field", "")
            sug["location"] = location
        sug["id"] = f"sug_{i:03d}"
        valid.append(sug)
    return valid
