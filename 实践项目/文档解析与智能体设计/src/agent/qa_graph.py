"""简历智能问答模块图：coaching 子图 + mock_interview 子图 + 入口路由"""

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver

from state.qa_state import QaState
from agent.qa import (
    intent_recognition,
    retrieval,
    answer_generate,
    memory_write,
)
from agent.mock_interview import (
    context_prepare,
    difficulty_grading,
    question_generate,
    ask,
    evaluate,
    summarize,
)


def should_continue(state: QaState) -> str:
    """交接模式：检查节点是否出错，有错则中断"""
    if state.get("error_data"):
        return "end"
    return "continue"


def build_coaching_engine():
    """构建面试辅导子图（intent → retrieval → answer → memory，任一节点失败即中断）"""
    graph = StateGraph(QaState)

    graph.add_node("intent_recognition", intent_recognition)
    graph.add_node("retrieval", retrieval)
    graph.add_node("answer_generate", answer_generate)
    graph.add_node("memory_write", memory_write)

    graph.set_entry_point("intent_recognition")

    graph.add_conditional_edges("intent_recognition", should_continue, {"continue": "retrieval", "end": END})
    graph.add_conditional_edges("retrieval", should_continue, {"continue": "answer_generate", "end": END})
    graph.add_conditional_edges("answer_generate", should_continue, {"continue": "memory_write", "end": END})

    graph.add_edge("memory_write", END)

    return graph.compile()


def _after_ask(state: QaState) -> str:
    """ask 后：有题则去 evaluate（中断等待作答），无题则 summarize"""
    if state.get("interview_status") == "done":
        return "summarize"
    return "evaluate"


def _after_evaluate(state: QaState) -> str:
    """evaluate 后：有待追问则先抛追问，否则看主问题是否耗尽"""
    if state.get("pending_follow_up"):
        return "ask"
    progress = state.get("progress") or {}
    if progress.get("asked", 0) >= progress.get("total", 0):
        return "summarize"
    return "ask"


def build_mock_interview_engine():
    """构建模拟面试子图（init → ask/evaluate 循环 → summarize，逐题交互）"""
    graph = StateGraph(QaState)

    graph.add_node("context_prepare", context_prepare)
    graph.add_node("difficulty_grading", difficulty_grading)
    graph.add_node("question_generate", question_generate)
    graph.add_node("ask", ask)
    graph.add_node("evaluate", evaluate)
    graph.add_node("summarize", summarize)

    graph.set_entry_point("context_prepare")
    graph.add_edge("context_prepare", "difficulty_grading")
    graph.add_edge("difficulty_grading", "question_generate")
    graph.add_edge("question_generate", "ask")

    graph.add_conditional_edges("ask", _after_ask, {"evaluate": "evaluate", "summarize": "summarize"})
    graph.add_conditional_edges("evaluate", _after_evaluate, {"ask": "ask", "summarize": "summarize"})

    graph.add_edge("summarize", END)

    # interrupt_before=evaluate：抛出题目后暂停，等待用户作答
    return graph.compile(checkpointer=InMemorySaver(), interrupt_before=["evaluate"])


def _route(state: QaState) -> str:
    """入口路由：按 request_type 分发到子图"""
    return state.get("request_type") or "coaching"


def build_qa_engine():
    """构建问答主图：入口路由 + 两个子图"""
    graph = StateGraph(QaState)

    graph.add_node("coaching", coaching_engine)
    graph.add_node("mock_interview", mock_interview_engine)

    graph.add_conditional_edges(START, _route, {"coaching": "coaching", "mock_interview": "mock_interview"})
    graph.add_edge("coaching", END)
    graph.add_edge("mock_interview", END)

    return graph.compile(checkpointer=InMemorySaver())


# 编译后的子图与主图
coaching_engine = build_coaching_engine()
mock_interview_engine = build_mock_interview_engine()
qa_engine = build_qa_engine()
