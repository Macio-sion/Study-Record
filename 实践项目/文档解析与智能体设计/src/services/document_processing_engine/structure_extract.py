"""节点四（结构化提取）业务代码：字段 Schema + LLM 提取 + 正则直提 + 置信度校准"""

import re
from typing import Optional, List

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from config.setting import get_settings
from llm.client import LLMClient
from prompts.structure_extract import STRUCTURE_EXTRACT_SYSTEM_PROMPT

settings = get_settings()

# 确定性字段正则（电话/邮箱不依赖 LLM）
PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

PENDING_THRESHOLD = 0.6
REQUIRED_FIELDS = ["personal.name", "personal.phone"]


# ---------------------------------------------------------------------------
# 字段 Schema（约束 LLM 输出结构）
# ---------------------------------------------------------------------------

class FieldValue(BaseModel):
    value: Optional[str] = None
    confidence: float = 0.0


class Personal(BaseModel):
    name: FieldValue = Field(default_factory=FieldValue)
    phone: FieldValue = Field(default_factory=FieldValue)
    email: FieldValue = Field(default_factory=FieldValue)
    gender: FieldValue = Field(default_factory=FieldValue)
    birth_date: FieldValue = Field(default_factory=FieldValue)
    city: FieldValue = Field(default_factory=FieldValue)
    political_status: FieldValue = Field(default_factory=FieldValue)


class Education(BaseModel):
    school: FieldValue = Field(default_factory=FieldValue)
    major: FieldValue = Field(default_factory=FieldValue)
    degree: FieldValue = Field(default_factory=FieldValue)
    start: FieldValue = Field(default_factory=FieldValue)
    end: FieldValue = Field(default_factory=FieldValue)
    gpa: FieldValue = Field(default_factory=FieldValue)
    ranking: FieldValue = Field(default_factory=FieldValue)
    courses: FieldValue = Field(default_factory=FieldValue)


class Experience(BaseModel):
    type: FieldValue = Field(default_factory=FieldValue)   # 实习/工作/项目/社团
    org: FieldValue = Field(default_factory=FieldValue)
    role: FieldValue = Field(default_factory=FieldValue)
    start: FieldValue = Field(default_factory=FieldValue)
    end: FieldValue = Field(default_factory=FieldValue)
    description: FieldValue = Field(default_factory=FieldValue)


class Skill(BaseModel):
    name: FieldValue = Field(default_factory=FieldValue)     # 技能名，如 Java、Python
    level: FieldValue = Field(default_factory=FieldValue)    # 熟练度（可选）


class Certificate(BaseModel):
    name: FieldValue = Field(default_factory=FieldValue)     # 证书名，如 英语四级、软件工程师
    level: FieldValue = Field(default_factory=FieldValue)    # 等级（可选）


class Award(BaseModel):
    name: FieldValue = Field(default_factory=FieldValue)


class ExtraField(BaseModel):
    name: str = ""                       # 字段名，如「求职意向」「专利」
    value: Optional[str] = None
    confidence: float = 0.0


class StructuredResume(BaseModel):
    personal: Personal = Field(default_factory=Personal)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    certificates: List[Certificate] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    summary: FieldValue = Field(default_factory=FieldValue)
    extra: List[ExtraField] = Field(default_factory=list)   # 动态扩展字段


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

STRUCTURE_EXTRACT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", STRUCTURE_EXTRACT_SYSTEM_PROMPT),
    ("human", "简历文本：\n{text}"),
])


# ---------------------------------------------------------------------------
# 正则直提确定性字段
# ---------------------------------------------------------------------------

def extract_contact_by_rules(text: str) -> dict:
    """正则直提电话/邮箱，确定性字段不依赖 LLM"""
    phone_match = PHONE_PATTERN.search(text)
    email_match = EMAIL_PATTERN.search(text)
    return {
        "phone": FieldValue(
            value=phone_match.group() if phone_match else None,
            confidence=0.99 if phone_match else 0.0,
        ),
        "email": FieldValue(
            value=email_match.group() if email_match else None,
            confidence=0.99 if email_match else 0.0,
        ),
    }


# ---------------------------------------------------------------------------
# LLM 结构化提取
# ---------------------------------------------------------------------------

def extract_structured(text: str, llm_client: LLMClient = None) -> StructuredResume:
    """从简历文本提取结构化字段（LLM 提取语义字段 + 正则直提确定性字段）"""
    if llm_client is None:
        llm_client = LLMClient(
            model_name=f"{settings.model_provider}:{settings.main_model}",
            temperature=0.0,  # 结构化提取用低温，提升稳定性
        )
    llm = llm_client.get_llm()
    structured_llm = llm.with_structured_output(StructuredResume)
    chain = STRUCTURE_EXTRACT_PROMPT | structured_llm
    result = chain.invoke({"text": text})

    # 正则直提电话/邮箱，覆盖 LLM 结果（确定性字段更可靠）
    contact = extract_contact_by_rules(text)
    result.personal.phone = contact["phone"]
    result.personal.email = contact["email"]

    return result


# ---------------------------------------------------------------------------
# 置信度校准 + pending 生成
# ---------------------------------------------------------------------------

def calibrate(result: StructuredResume, text: str) -> tuple[dict, list]:
    """生成 pending 待确认清单（电话/邮箱已由规则直提，无需再校准）"""
    pending = _build_pending(result)
    return result.model_dump(), pending


def _build_pending(result: StructuredResume) -> list:
    """生成待确认清单：低置信度字段 + 必填字段缺失"""
    pending = []
    seen = set()

    # 低置信度字段
    for field_path, field in _walk_fields(result):
        if field.value is None:
            continue
        if field.confidence < PENDING_THRESHOLD:
            pending.append({
                "field": field_path,
                "reason": "低置信度",
                "confidence": field.confidence,
            })
            seen.add(field_path)

    # 必填字段缺失
    for field_path in REQUIRED_FIELDS:
        field = _get_field(result, field_path)
        if field is None or field.value is None:
            pending.append({
                "field": field_path,
                "reason": "缺失",
                "confidence": 0.0,
            })

    return pending


def _walk_fields(model, prefix: str = ""):
    """递归遍历字段，yield (field_path, FieldValue)"""
    if isinstance(model, FieldValue):
        yield prefix, model
    elif isinstance(model, BaseModel):
        for name in model.model_fields:
            value = getattr(model, name)
            path = f"{prefix}.{name}" if prefix else name
            yield from _walk_fields(value, path)
    elif isinstance(model, list):
        for i, item in enumerate(model):
            yield from _walk_fields(item, f"{prefix}[{i}]")


def _get_field(result: StructuredResume, field_path: str):
    """按点号路径取字段值"""
    obj = result
    for part in field_path.split("."):
        obj = getattr(obj, part)
    return obj
