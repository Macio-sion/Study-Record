from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class SubState(TypedDict):
    """子图内部使用的状态"""
    messages: Annotated[list[BaseMessage], add_messages]
    sub_query: str        # 子图接收的查询
    sub_results: list[str]  # 子图内部产生的结果
    sub_iteration: int    # 子图内部迭代计数
    done: bool            # 子图内部完成标志

class ParentState(TypedDict):
    """父图的状态"""
    messages: Annotated[list[BaseMessage], add_messages]
    query: str            # 用户原始查询
    final_answer: str     # 最终答案
    sub_results: list[str]  # 从子图合并回来的结果

# ===== 子图节点 =====
def sub_node_a(state: SubState) -> dict:
    """子图节点A：接收输入，开始处理"""
    print(f"[子图] 节点A：接收查询 '{state.get('sub_query', '')}'")
    return {
        "messages": [AIMessage(content=f"子图收到查询：{state.get('sub_query', '')}")],
        "sub_results": [f"处理: {state.get('sub_query', '')}"],
        "sub_iteration": 1,
        "done": False
    }

def sub_node_b(state: SubState) -> dict:
    """子图节点B：深度处理"""
    iteration = state.get("sub_iteration", 0)
    print(f"[子图] 节点B：第{iteration}轮处理")
    return {
        "messages": [AIMessage(content=f"子图完成第{iteration}轮处理")],
        "sub_results": state.get("sub_results", []) + [f"第{iteration}轮结果"],
        "sub_iteration": iteration + 1,
        "done": iteration >= 2
    }

def sub_node_c(state: SubState) -> dict:
    """子图节点C：生成子图最终输出"""
    print(f"[子图] 节点C：生成最终结果")
    return {
        "messages": [AIMessage(content="子图处理完成！")],
        "done": True
    }

def sub_router(state: SubState) -> Literal["sub_b", "sub_c", END]:
    """子图路由"""
    if state.get("done", False):
        return "sub_c"
    else:
        return "sub_b"

# ===== 构建子图 =====
sub_graph = StateGraph(SubState)
sub_graph.add_node("sub_a", sub_node_a)
sub_graph.add_node("sub_b", sub_node_b)
sub_graph.add_node("sub_c", sub_node_c)

sub_graph.set_entry_point("sub_a")
sub_graph.add_edge("sub_a", "sub_b")
sub_graph.add_conditional_edges("sub_b", sub_router)
sub_graph.add_edge("sub_c", END)

sub_memory = MemorySaver()
sub_app = sub_graph.compile(checkpointer=sub_memory)

# ===== 父图节点 =====
def parent_entry(state: ParentState) -> dict:
    """父图入口节点"""
    print(f"[父图] 入口：用户查询 '{state.get('query', '')}'")
    return {"messages": [HumanMessage(content=state.get("query", ""))]}

def parent_call_subgraph(state: ParentState) -> dict:
    """
    调用子图的关键节点！
    子图被当作一个普通的 Runnable 节点。
    """
    print("[父图] 调用子图...")
    
    # 从父图 State 中提取需要传递给子图的数据
    sub_input = {
        "messages": state.get("messages", []),  # 也可以只传部分消息
        "sub_query": state.get("query", ""),
        "sub_results": [],
        "sub_iteration": 0,
        "done": False
    }
    
    # 调用子图（子图会独立执行，返回子图的最终 State）
    sub_result = sub_app.invoke(sub_input)
    
    print(f"[父图] 子图返回结果：{sub_result.get('sub_results', [])}")
    
    # 将子图的结果合并回父图
    return {
        "sub_results": sub_result.get("sub_results", []),
        "messages": sub_result.get("messages", [])
    }

def parent_finish(state: ParentState) -> dict:
    """父图结束节点"""
    print("[父图] 结束")
    return {
        "messages": [AIMessage(content=f"最终答案：{state.get('final_answer', '')}")]
    }

# ===== 构建父图 =====
parent_graph = StateGraph(ParentState)
parent_graph.add_node("entry", parent_entry)
parent_graph.add_node("subgraph", parent_call_subgraph)  # ← 子图作为节点
parent_graph.add_node("finish", parent_finish)

parent_graph.set_entry_point("entry")
parent_graph.add_edge("entry", "subgraph")
parent_graph.add_edge("subgraph", "finish")
parent_graph.add_edge("finish", END)

parent_memory = MemorySaver()
parent_app = parent_graph.compile(checkpointer=parent_memory)

def run_parent(query: str):
    """执行父图（内部调用子图）"""
    config = {"configurable": {"thread_id": "parent_session_001"}}
    
    print(f"\n{'='*60}")
    print(f"执行父图：查询 = {query}")
    print("="*60)
    
    result = parent_app.invoke({
        "messages": [],
        "query": query,
        "final_answer": f"根据子图处理，最终结果是...",
        "sub_results": []
    }, config=config)
    
    print("\n" + "="*60)
    print("【最终结果】")
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            print(f"AI: {msg.content}")
    print(f"子图结果: {result.get('sub_results', [])}")
    print("="*60)
    
    return result

# 测试
# run_parent("人工智能的发展趋势")

def test_isolation():
    """验证父图和子图的状态隔离"""
    print("\n" + "="*60)
    print("验证状态隔离")
    print("="*60)
    
    # 父图 State
    parent_state = {
        "messages": [HumanMessage(content="父图消息")],
        "query": "父图查询",
        "final_answer": "父图答案",
        "sub_results": ["父图已有结果"]
    }

    parent_config = {'configurable': {'thread_id': 'parent'}}
    
    # 子图 State（独立定义）
    sub_state = {
        "messages": [AIMessage(content="子图消息")],
        "sub_query": "子图查询",
        "sub_results": ["子图结果1", "子图结果2"],
        "sub_iteration": 5,
        "done": True
    }

    sub_config = {'configurable': {'thread_id': 'subgraph'}}

    sub_app.invoke(sub_state, config=sub_config)
    parent_app.invoke(parent_state, config=parent_config)
    
    print(f"父图 messages: {len(parent_state['messages'])} 条")
    print(f"子图 messages: {len(sub_state['messages'])} 条")
    print(f"父图 sub_results: {parent_state['sub_results']}")
    print(f"子图 sub_results: {sub_state['sub_results']}")
    print("\n✅ 父图和子图的 State 是独立的，字段不同、值不同")

test_isolation()