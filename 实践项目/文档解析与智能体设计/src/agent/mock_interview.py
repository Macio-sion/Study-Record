from state.qa_state import QaState
from services.qa_engine.question_generate import generate_questions
from services.qa_engine.evaluate import evaluate_answer
from services.qa_engine.summarize import summarize_report

# 难度分级映射（F-QA-004）
LEVEL_MAP = {
    "初级": {"tag": "初", "depth": "基础概念、工具使用、简单场景"},
    "中级": {"tag": "中", "depth": "方案设计、问题解决、团队协作"},
    "高级": {"tag": "高", "depth": "架构设计、技术选型、团队管理"},
    "专家": {"tag": "专家", "depth": "技术战略、行业趋势、创新突破"},
}

# 三类问题固定配比：技术 40% + 行为 30% + 案例 30%
DEFAULT_RATIO = {"technical": 0.4, "behavioral": 0.3, "case": 0.3}


def context_prepare(state: QaState) -> dict:
    """
    节点：上下文准备（模拟面试第一步）——校验经历充足性
    """
    fields = state.get("fields")
    if not fields:
        return {"error_data": {
            "code": "QA_NO_RESUME",
            "module": "context_prepare",
            "message": "请先上传并解析简历",
            "place": "fields",
        }}

    experience = fields.get("experience")
    if not experience:
        return {"error_data": {
            "code": "QA_NO_EXPERIENCE",
            "module": "context_prepare",
            "message": "简历信息不足，请补充关键经历后再开始模拟面试",
            "place": "experience",
        }}

    return {"context_ready": True}


def difficulty_grading(state: QaState) -> dict:
    """
    节点：难度分级（模拟面试第二步）——level → 难度画像
    """
    level = state.get("level") or "中级"
    profile = LEVEL_MAP.get(level, LEVEL_MAP["中级"])
    return {
        "difficulty_profile": {
            "tag": profile["tag"],
            "depth": profile["depth"],
            "ratio": DEFAULT_RATIO,
        }
    }


def question_generate(state: QaState) -> dict:
    """
    节点：问题生成（模拟面试第三步）——生成技术/行为/案例三类面试问题
    """
    fields = state.get("fields")
    if not fields:
        return {"error_data": {
            "code": "QA_NO_RESUME",
            "module": "question_generate",
            "message": "请先上传并解析简历",
            "place": "fields",
        }}

    jd = state.get("jd") or ""
    difficulty_profile = state.get("difficulty_profile") or {}
    return generate_questions(fields, jd, difficulty_profile)


def ask(state: QaState) -> dict:
    """
    节点：提问（模拟面试第四步）——先抛追问（若有），再抛下一道主问题（多轮状态机）
    """
    # 若有待追问，先抛追问（继承主问题的分类）
    pending = state.get("pending_follow_up")
    if pending:
        base = state.get("current_question") or {}
        return {
            "current_question": {
                "id": base.get("id", ""),
                "question": pending,
                "category": base.get("category", ""),
                "type": "follow_up",
            },
            "pending_follow_up": None,  # 清除待追问
            "interview_status": "asking",
        }

    # 否则抛下一道主问题
    question_list = state.get("question_list") or {}
    all_questions = _flatten_questions(question_list)
    total = len(all_questions)

    if total == 0:
        return {"interview_status": "done"}

    progress = state.get("progress") or {"asked": 0, "total": total}
    asked = progress.get("asked", 0)

    if asked >= total:
        return {"interview_status": "done"}

    current = dict(all_questions[asked])
    current["type"] = "main"
    return {
        "current_question": current,
        "progress": {"asked": asked + 1, "total": total},
        "interview_status": "asking",
    }


def _flatten_questions(question_list: dict) -> list:
    """把三类问题按技术→行为→案例顺序展开成一维列表，并给每题打上 category 标签"""
    order = []
    for category in ("technical", "behavioral", "case"):
        for q in question_list.get(category) or []:
            item = dict(q)
            item["category"] = category
            order.append(item)
    return order


def evaluate(state: QaState) -> dict:
    """
    节点：追问评估（模拟面试第五步）——点评/评分 + 动态追问，并累积问答记录
    """
    current_question = state.get("current_question") or {}
    question_text = current_question.get("question", "")
    user_answer = state.get("user_answer") or ""
    qtype = current_question.get("type", "main")
    if not question_text or not user_answer:
        return {}  # 无问题或未作答，跳过

    result = evaluate_answer(question_text, user_answer)
    feedback = result["feedback"]

    # 累积问答记录，供总结报告使用
    qa_records = list(state.get("qa_records") or [])
    qa_records.append({
        "question": question_text,
        "answer": user_answer,
        "score": feedback.get("score"),
        "category": current_question.get("category", ""),
    })

    # 追问逻辑：主问题回答后若有追问则设待追问；追问回答后清除待追问
    follow_up = feedback.get("follow_up", "")
    if qtype == "main" and follow_up:
        return {"feedback": feedback, "qa_records": qa_records, "pending_follow_up": follow_up}
    return {"feedback": feedback, "qa_records": qa_records, "pending_follow_up": None}


def summarize(state: QaState) -> dict:
    """
    节点：总结报告（模拟面试第六步）——汇总问答记录生成面试评估报告
    """
    qa_records = state.get("qa_records") or []
    if not qa_records:
        return {"report": None, "interview_status": "done"}

    report = summarize_report(qa_records)
    report["qa_records"] = qa_records
    return {"report": report, "interview_status": "done"}
