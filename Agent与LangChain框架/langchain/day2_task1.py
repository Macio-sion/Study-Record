from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class LoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    iteration: int        # 当前已执行轮数
    max_iterations: int   # 最大轮数
    should_continue: bool # 是否继续循环

def think(state: LoopState) -> dict:
    """
    思考节点：
    1. 增加迭代计数器
    2. 判断是否还需要继续
    """
    current = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 3)
    new_iter = current + 1
    
    # 判断是否继续
    should_continue = new_iter <= max_iter
    
    if should_continue:
        content = f"💭 第{new_iter}轮思考：信息还不够，需要继续搜索。"
    else:
        content = f"💭 第{new_iter}轮思考：信息已充足，准备给出答案。"
    
    print(f"[思考] 第{new_iter}轮，继续={should_continue}")
    
    return {
        "messages": [AIMessage(content=content)],
        "iteration": new_iter,
        "should_continue": should_continue
    }

def act(state: LoopState) -> dict:
    """
    行动节点：模拟工具调用
    """
    iteration = state.get("iteration", 0)
    content = f"🔧 执行第{iteration}轮行动：搜索相关信息..."
    print(f"[行动] 第{iteration}轮执行")
    
    return {
        "messages": [AIMessage(content=content)]
    }

def finish(state: LoopState) -> dict:
    """
    结束节点：生成最终答案
    """
    total = state.get("iteration", 0)
    content = f"✅ 任务完成！共执行了{total}轮思考-行动。最终答案：..."
    print(f"[结束] 共执行{total}轮")
    
    return {
        "messages": [AIMessage(content=content)]
    }

def root(state: LoopState) -> Literal["think", "act", "finish", END]:
    """
    根节点：根据 should_continue 决定下一步
    """
    should_continue = state.get("should_continue", True)
    
    if should_continue:
        print("[路由] 继续循环 -> act")
        return "act"
    else:
        print("[路由] 循环结束 -> finish")
        return "finish"
    
graph = StateGraph(LoopState)

graph.add_node("think", think)
graph.add_node("act", act)
graph.add_node("finish", finish)

graph.set_entry_point("think")

graph.add_conditional_edges("think", root)

graph.add_edge("finish", END)
graph.add_edge("act", "think")

app = graph.compile()

result = app.invoke(
    {
        "messages": [HumanMessage(content="请帮我完成一个复杂任务。")],
    "iteration": 0,
    "max_iterations": 3, 
    "should_continue": True
    }
)