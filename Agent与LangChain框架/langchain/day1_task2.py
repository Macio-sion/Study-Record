from typing import Annotated, TypedDict, Literal, List
from langgraph.graph import StateGraph, END, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class FullState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    intent: str
    results: List[str]
    iteration: int
    approved: bool

# ===== 节点 =====
def parse_intent(state: FullState) -> dict:
    msg = state["messages"][-1].content
    return {"query": msg, "intent": "search" if "查询" in msg else "unknown"}

def search(state: FullState) -> dict:
    return {"results": [f"结果{state.get("iteration", 0)+1}: ..."], "iteration": state.get("iteration", 0) + 1}

def analyze(state: FullState) -> dict:
    return {"messages": [AIMessage(content="分析完成")]}

def approve(state: FullState) -> dict:
    return {"approved": True, "messages": [AIMessage(content="已批准")]}

def unknown(state: FullState) -> dict:
    return {"messages": [AIMessage(content="无法识别的意图")]}

# ===== 路由 =====
def route_intent(state: FullState) -> Literal["search", "unknown"]:
    print(state["intent"])
    if state["intent"] == "search":
        return "search" if state.get("iteration", 0) < 3 else "analyze"
    return "unknown"

def route_after_analyze(state: FullState) -> Literal["approve"]:
    return "approve" if not state.get("approved") else END

# ===== 构建 =====
graph = StateGraph(FullState)
graph.add_node("parse", parse_intent)
graph.add_node("search", search)
graph.add_node("analyze", analyze)
graph.add_node("approve", approve)
graph.add_node("unknown", unknown)

graph.set_entry_point("parse")
graph.add_conditional_edges("parse", route_intent)
graph.add_edge("search", "analyze")
graph.add_conditional_edges("analyze", route_after_analyze)
graph.add_edge("approve", END)

app = graph.compile(checkpointer=MemorySaver())

# ===== 执行 =====
config = {"configurable": {"thread_id": "demo"}}
result = app.invoke(
    {"messages": [HumanMessage(content="查询北京天气")]},
    config=config
)
print(result)