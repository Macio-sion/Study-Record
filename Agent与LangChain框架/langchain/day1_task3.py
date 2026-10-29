from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class MyState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    count: int

def node_a(state: MyState) -> dict:
    """
    读取当前节点的count, 并将其加1，返回新的count值
    """
    new_count = state.get("count", 0) + 1
    print(f"节点node_a: 当前count={state.get('count', 0)}, 新count={new_count}")
    return {"count": new_count, "messages": [AIMessage(content=f"Count is now {new_count}")]}

def node_b(state: MyState) -> dict:
    """
    继续处理count, 并将其加1，返回新的count值
    """
    new_count = state.get("count", 0) + 1
    print(f"节点node_b: 当前count={state.get('count', 0)}, 新count={new_count}")
    return {"count": new_count, "messages": [AIMessage(content=f"Count is now {new_count}")]}

def node_c(state: MyState) -> dict:
    """
    继续处理count, 并将其加1，返回新的count值
    """
    new_count = state.get("count", 0) + 1
    print(f"节点node_c: 当前count={state.get('count', 0)}, 新count={new_count}")
    return {"count": new_count, "messages": [AIMessage(content=f"Count is now {new_count}")]}

graph = StateGraph(MyState)

graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.add_node("c", node_c)

graph.set_entry_point("a")
graph.add_edge("a", "b")
graph.add_edge("b", "c")
graph.add_edge("c", END)

app = graph.compile()

result = app.invoke(
    {"messages": [HumanMessage(content="Start counting")], "count": 0}
)

print(result)