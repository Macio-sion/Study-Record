"""SKILL 库：渐进式披露的知识模块（name/description/检索项 + load_skill 工具 + 后端检索器）"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional, TypedDict

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.tools import tool
from langchain_core.messages import SystemMessage

# 知识域
DOMAIN_COACHING = "coaching"    # 候选人答题知识
DOMAIN_INTERVIEW = "interview"  # 面试官出题知识

# 默认 md 知识库文件
COACHING_KB_FILE = str(Path(__file__).resolve().parents[3] / "test" / "datas" / "interview_kb.md")
INTERVIEW_QB_FILE = str(Path(__file__).resolve().parents[3] / "test" / "datas" / "interview_question_bank.md")


class Skill(TypedDict, total=False):
    """SKILL 元数据：name/description 用于渐进式披露；source_type + source_ref（检索项）用于 load 时后端检索"""

    name: str            # 技能名
    description: str     # 作用描述（一级披露，供 LLM 匹配）
    domain: str          # 知识域：coaching / interview
    source_type: str     # 检索来源类型：md / db / vector
    source_ref: str      # 检索项：定位 content（md 章节 / 表名 / collection 名）
    source_file: str     # md 源的文件路径（仅 md 源需要）


# SKILL 库（元数据）。content 不写死，load_skill 时按检索项后端检索得到
SKILLS: List[Skill] = [
    # 候选人答题知识（coaching）
    {"name": "star_framework", "description": "STAR 法则答题框架（行为面/案例面）", "domain": DOMAIN_COACHING, "source_type": "md", "source_ref": "STAR 法则答题框架", "source_file": COACHING_KB_FILE},
    {"name": "tech_framework", "description": "技术面试答题框架", "domain": DOMAIN_COACHING, "source_type": "md", "source_ref": "技术面试答题框架", "source_file": COACHING_KB_FILE},
    {"name": "behavior_tips", "description": "行为面试常见题答题要点", "domain": DOMAIN_COACHING, "source_type": "md", "source_ref": "行为面试答题要点", "source_file": COACHING_KB_FILE},
    {"name": "case_tips", "description": "案例/项目面试答题要点与高频追问", "domain": DOMAIN_COACHING, "source_type": "md", "source_ref": "案例/项目面试答题要点", "source_file": COACHING_KB_FILE},
    {"name": "general_tips", "description": "通用面试答题技巧", "domain": DOMAIN_COACHING, "source_type": "md", "source_ref": "通用面试答题技巧", "source_file": COACHING_KB_FILE},
    # 面试官出题知识（interview）
    {"name": "tech_question_tips", "description": "技术面出题要点", "domain": DOMAIN_INTERVIEW, "source_type": "md", "source_ref": "技术面出题要点", "source_file": INTERVIEW_QB_FILE},
    {"name": "behavior_question_tips", "description": "行为面出题要点", "domain": DOMAIN_INTERVIEW, "source_type": "md", "source_ref": "行为面出题要点", "source_file": INTERVIEW_QB_FILE},
    {"name": "case_question_tips", "description": "案例面出题要点", "domain": DOMAIN_INTERVIEW, "source_type": "md", "source_ref": "案例面出题要点", "source_file": INTERVIEW_QB_FILE},
    {"name": "difficulty_standards", "description": "难度分级出题标准", "domain": DOMAIN_INTERVIEW, "source_type": "md", "source_ref": "难度分级出题标准", "source_file": INTERVIEW_QB_FILE},
]


class ContentRetriever(ABC):
    """后端内容检索器：按 skill 的检索项从不同来源取回 content 文本"""

    source_type: str = ""

    @abstractmethod
    def retrieve(self, skill: Skill, question: str = None) -> str:
        """按 skill 检索项检索，返回内容文本"""


class MdContentRetriever(ContentRetriever):
    """md 文件：读取文件，按 ## 标题匹配 source_ref 返回章节正文"""

    source_type = "md"

    def retrieve(self, skill: Skill, question: str = None) -> str:
        file_path = skill.get("source_file") or COACHING_KB_FILE
        for chunk in _read_markdown_chunks(file_path):
            if chunk["field"] == skill["source_ref"]:
                return chunk["text"]
        return ""


class DbContentRetriever(ContentRetriever):
    """关系型数据库：按 source_ref（表名/查询模板）检索，后续接入"""

    source_type = "db"

    def retrieve(self, skill: Skill, question: str = None) -> str:
        return ""


class VectorContentRetriever(ContentRetriever):
    """向量数据库：按 source_ref（collection）向量检索，后续接入"""

    source_type = "vector"

    def retrieve(self, skill: Skill, question: str = None) -> str:
        return ""


# source_type -> 后端检索器
RETRIEVERS = {
    "md": MdContentRetriever(),
    "db": DbContentRetriever(),
    "vector": VectorContentRetriever(),
}


def find_skill(name: str) -> Optional[Skill]:
    """按 name 查找 skill 元数据"""
    for skill in SKILLS:
        if skill["name"] == name:
            return skill
    return None


def skills_prompt(domain: Optional[str] = None) -> str:
    """一级披露：指定域（或全部）skill 的 name + description（不加载 content）"""
    skills = [s for s in SKILLS if domain is None or s.get("domain") == domain]
    lines = [f"- **{s['name']}**: {s['description']}" for s in skills]
    return "\n".join(lines)


@tool
def load_skill(skill_name: str) -> str:
    """加载指定技能的完整内容。

    当需要某类面试答题/出题的详细框架、要点或技巧时，按 name 加载其完整内容。

    Args:
        skill_name: 技能名（如 star_framework、tech_framework、tech_question_tips、difficulty_standards 等）
    """
    skill = find_skill(skill_name)
    if skill is None:
        available = ", ".join(s["name"] for s in SKILLS)
        return f"未找到技能 {skill_name}，可用技能：{available}"
    retriever = RETRIEVERS.get(skill["source_type"])
    if retriever is None:
        return f"技能 {skill_name} 的检索源未实现"
    content = retriever.retrieve(skill)
    return f"已加载技能 {skill_name}：\n{content}" if content else f"技能 {skill_name} 暂无内容"


def load_domain_skills(domain: str) -> str:
    """确定性加载指定域所有 skill 的完整 content（用于需要全量知识的场景，如出题）"""
    parts = []
    for skill in SKILLS:
        if skill.get("domain") != domain:
            continue
        retriever = RETRIEVERS.get(skill["source_type"])
        if retriever is None:
            continue
        content = retriever.retrieve(skill)
        if content:
            parts.append(f"### {skill['description']}\n{content}")
    return "\n\n".join(parts)


class SkillMiddleware(AgentMiddleware):
    """渐进式披露中间件：每次模型调用前把指定域 skill 的 name+description 注入系统提示词，并暴露 load_skill 工具"""

    tools = [load_skill]

    def __init__(self, domain: str) -> None:
        self.skills_prompt = skills_prompt(domain)

    def wrap_model_call(self, request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]):
        skill_addendum = (
            f"\n\n## 可用技能\n\n{self.skills_prompt}\n\n"
            "当你需要相关领域的详细框架、要点或技巧时，调用 load_skill 工具按 name 加载对应技能的完整内容。"
        )
        new_content = request.system_message.content + skill_addendum
        modified_request = request.override(system_message=SystemMessage(content=new_content))
        return handler(modified_request)


def _read_markdown_chunks(file_path: str) -> List[dict]:
    """读取 md 文件并按 ## 二级标题分块，返回 [{field, text}]"""
    path = Path(file_path)
    if not path.exists():
        return []
    return _split_markdown(path.read_text(encoding="utf-8"))


def _split_markdown(content: str) -> List[dict]:
    """按 ## 二级标题把 md 内容切成知识块，返回 [{field, text}]"""
    chunks: List[dict] = []
    current_title = None
    current_lines: List[str] = []
    for line in content.splitlines():
        if line.startswith("## "):
            if current_title is not None:
                text = "\n".join(current_lines).strip()
                if text:
                    chunks.append({"field": current_title, "text": text})
            current_title = line[3:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append({"field": current_title, "text": text})
    return chunks
