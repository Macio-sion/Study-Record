"""简历解析引擎子图（Pipeline：五节点串行链，交接模式 Handoff）"""

from langgraph.graph import StateGraph, END

from state.resume_state import ResumeState
from agent.files_parse import (
    validate_file,
    parse_file,
    layout_process,
    structure_extract,
    validate_result,
    should_continue,
)

def build_parse_engine():
    """构建简历解析引擎子图（五节点串行链，任一节点失败即中断）"""
    graph = StateGraph(ResumeState)

    # 五个节点
    graph.add_node("validate_file", validate_file)
    graph.add_node("parse_file", parse_file)
    graph.add_node("layout_process", layout_process)
    graph.add_node("structure_extract", structure_extract)
    graph.add_node("validate_result", validate_result)

    # 入口
    graph.set_entry_point("validate_file")

    # 条件边：每个节点后检查 error_data，有错中断，无错继续（交接模式）
    graph.add_conditional_edges(
        "validate_file", should_continue,
        {"continue": "parse_file", "end": END},
    )
    graph.add_conditional_edges(
        "parse_file", should_continue,
        {"continue": "layout_process", "end": END},
    )
    graph.add_conditional_edges(
        "layout_process", should_continue,
        {"continue": "structure_extract", "end": END},
    )
    graph.add_conditional_edges(
        "structure_extract", should_continue,
        {"continue": "validate_result", "end": END},
    )

    # 终点：validate_result 是最后一个节点，直接结束
    graph.add_edge("validate_result", END)

    return graph.compile()


# 编译后的解析引擎子图，供主图作为节点挂载复用
parse_engine = build_parse_engine()
