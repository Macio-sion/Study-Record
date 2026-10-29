from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_name: str
    count: int

def chat_node(state: ChatState) -> dict:
    """
    对话节点：处理用户消息，记住名字
    """
    last_msg = state["messages"][-1]
    content = last_msg.content
    
    # 提取名字：如果用户说"我叫X"
    if "我叫" in content:
        name = content.split("我叫")[-1].strip()
        response = f"你好，{name}！很高兴认识你。"
        return {
            "messages": [AIMessage(content=response)],
            "user_name": name,
            "chat_count": state.get("chat_count", 0) + 1
        }
    
    # 如果用户问"我叫什么名字"
    if "咕咕嘎嘎" in content:
        name = state.get("user_name", "未知")
        if name != "未知":
            response = f"你叫{name}啊，我记得！"
        else:
            response = "我还不知道你的名字呢，你可以告诉我（说'我叫XXX'）"
        return {
            "messages": [AIMessage(content=response)],
            "chat_count": state.get("chat_count", 0) + 1
        }
    
    # 普通对话
    response = f"收到：{content}。有什么我可以帮你的？"
    return {
        "messages": [AIMessage(content=response)],
        "chat_count": state.get("chat_count", 0) + 1
    }

graph = StateGraph(ChatState)

graph.add_node("chat", chat_node)

graph.set_entry_point("chat")

graph.add_edge("chat", END)

app = graph.compile(checkpointer=MemorySaver())

def inspect_state(thread_id: str):
    """查看指定会话的检查点状态"""
    config = {"configurable": {"thread_id": thread_id}}
    
    # 获取最新状态
    state = app.get_state(config)
    
    if state is None:
        print(f"会话 {thread_id} 不存在或没有检查点")
        return
    print(state)
    print(f"\n=== 会话 {thread_id} 的检查点 ===")
    print(f"消息数量: {len(state.values.get('messages', []))}")
    print(f"用户名: {state.values.get('user_name', '未设置')}")
    print(f"对话轮数: {state.values.get('chat_count', 0)}")
    
    # 打印最后3条消息
    messages = state.values.get('messages', [])
    if messages:
        print("最近消息:")
        for msg in messages[-3:]:
            print(f"  [{msg.type}] {msg.content[:50]}...")

# 查看会话1的状态
# inspect_state("user_001")

# # 查看不存在的会话
# inspect_state("non_existent")

# def chat_session(thread_id: str):
#     """一个独立的对话会话"""
#     config = {"configurable": {"thread_id": thread_id}}
    
#     def talk(user_input: str):
#         result = app.invoke(
#             {"messages": [HumanMessage(content=user_input)]},
#             config=config
#         )
#         # 获取最新回复
#         last_msg = result["messages"][-1]
#         if isinstance(last_msg, AIMessage):
#             print(f"助手: {last_msg.content}")
#         return result
    
#     print(f"\n{'='*50}")
#     print(f"会话开始 (thread_id: {thread_id})")
#     print("="*50)
    
#     talk("你好！")
#     talk("我叫小明")
#     talk("咕咕嘎嘎？")
#     talk("今天天气怎么样？")
    
#     return talk

# # 执行一个会话
# print("\n=== 会话1 ===")
# result1 = chat_session("user_001")
# print(result1)

# 会话1：用户A
config_a = {"configurable": {"thread_id": "user_a"}}
result_a = app.invoke(
    {"messages": [HumanMessage("我叫张三")]},
    config=config_a
)
print(f"用户A: {result_a['messages'][-1].content}")

result_a = app.invoke(
    {"messages": [HumanMessage("咕咕嘎嘎？")]},
    config=config_a
)
print(f"用户A: {result_a['messages'][-1].content}")

# 会话2：用户B（完全独立）
config_b = {"configurable": {"thread_id": "user_b"}}
result_b = app.invoke(
    {"messages": [HumanMessage("咕咕嘎嘎？")]},
    config=config_b
)
print(f"\n用户B: {result_b['messages'][-1].content}")

inspect_state("user_a")

inspect_state("user_b")

# # 模拟：第一次执行（部分完成）
# config = {"configurable": {"thread_id": "user_recovery"}}

# print("=== 第一次执行（模拟进程运行中）===")
# result1 = app.invoke(
#     {"messages": [HumanMessage("我叫李四")]},
#     config=config
# )
# print(f"助手: {result1['messages'][-1].content}")

# # 模拟：进程重启，但使用同一个 thread_id
# print("\n=== 进程恢复（使用相同 thread_id）===")
# result2 = app.invoke(
#     {"messages": [HumanMessage("咕咕嘎嘎？")]},
#     config=config  # 同一个 config
# )
# print(f"助手: {result2['messages'][-1].content}")

# # 模拟：新的进程，新的 thread_id
# print("\n=== 新进程（新 thread_id）===")
# new_config = {"configurable": {"thread_id": "user_new"}}
# result3 = app.invoke(
#     {"messages": [HumanMessage("我叫什么名字？")]},
#     config=new_config
# )
# print(f"助手: {result3['messages'][-1].content}")