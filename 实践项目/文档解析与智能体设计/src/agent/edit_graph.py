"""简历智能生成与优化模块图：入口路由 + 生成/优化两个子图 + 应用/对比节点"""

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver

from state.edit_state import EditState
from agent.edit import info_collect, generate, optimize, apply, diff, should_continue


def build_generate_engine():
    """简历生成子图：信息获取 → 简历生成（串行链，交接模式）"""
    graph = StateGraph(EditState)

    graph.add_node("info_collect", info_collect)
    graph.add_node("generate", generate)

    graph.set_entry_point("info_collect")
    graph.add_conditional_edges("info_collect", should_continue, {"continue": "generate", "end": END})
    graph.add_edge("generate", END)

    return graph.compile()


def build_optimize_engine():
    """逐条优化子图：信息获取 → 逐条优化（串行链，交接模式）"""
    graph = StateGraph(EditState)

    graph.add_node("info_collect", info_collect)
    graph.add_node("optimize", optimize)

    graph.set_entry_point("info_collect")
    graph.add_conditional_edges("info_collect", should_continue, {"continue": "optimize", "end": END})
    graph.add_edge("optimize", END)

    return graph.compile()


def _route(state: EditState) -> str:
    """入口路由：按 request_type 分发到子流程"""
    return state.get("request_type") or "optimize"


def build_edit_engine():
    """构建生成与优化主图：入口路由 + 两个子图 + 应用/对比节点"""
    graph = StateGraph(EditState)

    graph.add_node("generate", generate_engine)
    graph.add_node("optimize", optimize_engine)
    graph.add_node("apply", apply)
    graph.add_node("diff", diff)

    graph.add_conditional_edges(
        START, _route,
        {"generate": "generate", "optimize": "optimize", "apply": "apply", "diff": "diff"},
    )
    for name in ("generate", "optimize", "apply", "diff"):
        graph.add_edge(name, END)

    return graph.compile(checkpointer=InMemorySaver())


# 编译后的子图与主图
generate_engine = build_generate_engine()
optimize_engine = build_optimize_engine()
edit_engine = build_edit_engine()
