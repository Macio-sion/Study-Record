from state.qa_state import QaState
from services.qa_engine.intent import recognize_intent
from services.qa_engine.retrieval import flatten_fields
from services.qa_engine.answer import generate_answer
from services.qa_engine.memory import desensitize, new_session_id, memory_store


def intent_recognition(state: QaState) -> dict:
    """
    节点：意图识别（面试辅导子图第一步）——判断面试题类型（技术面/行为面/案例面/通用）
    """
    question = state.get("question")
    if not question:
        return {"error_data": {
            "code": "QA_NO_QUESTION",
            "module": "intent_recognition",
            "message": "问题为空，请先输入面试题",
            "place": "question",
        }}

    return recognize_intent(question)


def retrieval(state: QaState) -> dict:
    """
    节点：简历检索（面试辅导子图第二步）——结构化简历展开为条目级检索块
    """
    fields = state.get("fields")
    if not fields:
        return {"error_data": {
            "code": "QA_NO_RESUME",
            "module": "retrieval",
            "message": "请先上传并解析简历",
            "place": "fields",
        }}

    return {"retrieved": flatten_fields(fields)}


def answer_generate(state: QaState) -> dict:
    """
    节点：回答生成（面试辅导子图第三步）——agent 以候选人身份生成参考答案
    """
    question = state.get("question")
    if not question:
        return {"error_data": {
            "code": "QA_NO_QUESTION",
            "module": "answer_generate",
            "message": "问题为空，请先输入面试题",
            "place": "question",
        }}

    retrieved = state.get("retrieved")
    if not retrieved:
        return {"error_data": {
            "code": "QA_RETRIEVE_EMPTY",
            "module": "answer_generate",
            "message": "未找到可用的简历信息，请先上传并解析简历",
            "place": "retrieved",
        }}

    intent = state.get("intent") or "通用"
    return generate_answer(question, intent, retrieved)


def memory_write(state: QaState) -> dict:
    """
    节点：记忆持久化（面试辅导子图第四步）——写入多轮对话上下文，敏感信息脱敏
    """
    question = state.get("question")
    answer = state.get("answer")
    if not question or not answer:
        return {}  # 无内容可记，直接跳过

    session_id = state.get("session_id") or new_session_id()
    turn = {
        "question": desensitize(question),
        "answer": desensitize(answer),
    }
    history = memory_store.append(session_id, turn)
    return {"session_id": session_id, "history": history}
