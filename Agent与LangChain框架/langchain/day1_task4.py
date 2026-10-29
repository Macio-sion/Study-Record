from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class RouterState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    results: list[str]
    iteration: int
    approved: bool

def parse_intent(state: RouterState) -> dict:
    """
    解析用户意图，设置 state.intent
    """
    last_msg = state["messages"][-1]
    content = last_msg.content
    
    # 简单的关键词匹配
    if "天气" in content or "weather" in content:
        intent = "weather"
    elif "笑话" in content or "joke" in content:
        intent = "joke"
    elif "股票" in content or "stock" in content:
        intent = "stock"
    else:
        intent = "unknown"
    
    print(f"[解析] 识别意图: {intent}")
    return {"intent": intent}

def route_by_intent(state: RouterState) -> Literal["weather", "joke", "stock", "unknown", END]:
    """
    路由函数：根据意图决定下一步
    """
    intent = state.get("intent", "unknown")
    print(f"[路由] 跳转到: {intent}")
    
    if intent == "weather":
        return "weather"
    elif intent == "joke":
        return "joke"
    elif intent == "stock":
        return "stock"
    else:
        return "unknown"
    
def handle_weather(state: RouterState) -> dict:
    """处理天气查询"""
    count = state.get("iteration", 0) + 1
    return {
        "messages": [AIMessage(content="🌤️ 北京今天晴天，25°C，空气质量良好。")],
        "iteration": count
    }

def handle_joke(state: RouterState) -> dict:
    """处理笑话请求"""
    count = state.get("iteration", 0) + 1
    return {
        "messages": [AIMessage(content="😂 为什么程序员总是混淆万圣节和圣诞节？因为 Oct 31 = Dec 25！")],
        "iteration": count
    }

def handle_stock(state: RouterState) -> dict:
    """处理股票查询"""
    count = state.get("iteration", 0) + 1
    return {
        "messages": [AIMessage(content="📈 上证指数今日报收3250点，上涨0.5%。")],
        "iteration": count
    }

def handle_unknown(state: RouterState) -> dict:
    """处理未知意图"""
    count = state.get("iteration", 0) + 1
    return {
        "messages": [AIMessage(content="❓ 我没理解你的意思。请尝试问天气、笑话或股票。")],
        "iteration": count
    }

graph = StateGraph(RouterState)

graph.add_node("parse", parse_intent)
graph.add_node("weather", handle_weather)
graph.add_node("joke", handle_joke)
graph.add_node("stock", handle_stock)
graph.add_node("unknown", handle_unknown)

graph.set_entry_point("parse")

graph.add_conditional_edges("parse", route_by_intent)

graph.add_edge("weather", END)
graph.add_edge("joke", END)
graph.add_edge("stock", END)
graph.add_edge("unknown", END)


app = graph.compile()

result = app.invoke(
    {"messages": [HumanMessage(content="请讲个笑话。")], "iteration": 0, "approved": False}
)

print(result)