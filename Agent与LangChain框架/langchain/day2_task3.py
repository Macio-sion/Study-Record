from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class ApprovalState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    draft: str              # 草稿内容
    approved: bool          # 是否批准
    reviewer_comment: str   # 审核意见（可选）
    next_node: str          # 下一步节点

def generate_draft(state: ApprovalState) -> dict:
    """节点1：生成草稿"""
    draft = """
    尊敬的各位同事：
    
    本季度公司业绩稳步增长，各项目进展顺利。
    感谢全体员工的辛勤付出！
    
    特此通报。
    """
    print(f"[生成草稿] 已生成公告草稿")
    return {
        "messages": [AIMessage(content="📄 已生成公告草稿，等待审核。")],
        "draft": draft,
        "approved": False
    }

def publish(state: ApprovalState) -> dict:
    """节点2：发布（只有 approved=True 时才会执行到这里）"""
    print(f"[发布] 草稿已通过审核，正在发布...")
    return {
        "messages": [AIMessage(content="✅ 公告已成功发布！")]
    }

def reject(state: ApprovalState) -> dict:
    """节点3：拒绝（只有 approved=False 时才会执行到这里）"""
    comment = state.get("reviewer_comment", "无具体意见")
    print(f"[拒绝] 草稿被拒绝，意见：{comment}")
    return {
        "messages": [AIMessage(content=f"❌ 草稿已被拒绝。审核意见：{comment}")]
    }

def node_router(state: ApprovalState) -> dict:
    """
    节点路由函数，根据 approved 状态决定下一步执行哪个节点
    """
    if state.get("approved", False):
        return {"next_node": "publish"}
    else:
        return {"next_node": "reject"}

def router(state: ApprovalState) -> Literal["reject", "publish"]:
    """
    """
    return state.get("next_node", "reject")
        
    
graph = StateGraph(ApprovalState)

graph.add_node("generate_draft", generate_draft)
graph.add_node("publish", publish)
graph.add_node("reject", reject)
graph.add_node("router", node_router)

graph.set_entry_point("generate_draft")

graph.add_edge("generate_draft", "router")
graph.add_conditional_edges("router", router)
graph.add_edge("publish", END)
graph.add_edge("reject", END)

app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_after=["generate_draft"],
    interrupt_before=["publish"], 
)

def manual_review_demo():
    """演示手动介入的每一步"""
    thread_id = "manual_demo"
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n" + "="*60)
    print("人工介入演示")
    print("="*60)
    
    # 步骤1：执行到中断点
    print("\n[1] 执行 generate 节点...")
    result = app.invoke({
        "messages": [HumanMessage(content="生成周报")],
        "draft": "",
        "approved": False,
        "reviewer_comment": ""
    }, config=config)
    
    print(f"  生成完成，当前状态:")
    print(f"    draft: {result.get('draft', '')[:50]}...")
    print(f"    approved: {result.get('approved')}")
    
    # 步骤2：获取当前状态
    print("\n[2] 获取检查点状态...")
    state = app.get_state(config)
    print(f"    next节点: {state.next}")  # 应该显示 generate 之后的下一个节点
    
    # 步骤3：查看可用的操作
    print("\n[3] 人工审核中...")
    print(f"    草稿内容: {state.values.get('draft', '')}")
    print(f"    当前批准状态: {state.values.get('approved')}")
    
    # # 步骤4：人工决定通过
    # print("\n[4] 审核通过，修改状态...")
    # state.values["approved"] = True
    # state.values["reviewer_comment"] = "内容准确，可以发布"
    # app.update_state(config, state.values)
    # print(f"    已更新: approved={state.values['approved']}")

    # 步骤4：人工决定否决
    print("\n[4] 审核否决，修改状态...")
    state.values["approved"] = True
    state.values["reviewer_comment"] = "批准"
    app.update_state(config, state.values)
    print(f"    已更新: approved={state.values['approved']}")
    
    # 步骤5：继续执行
    print("\n[5] 继续执行...")
    temp = app.invoke(None, config=config)


    final = app.invoke(None, config=config)
    print(f"    最终结果: {final['messages'][-1].content}")
    
    print("\n✅ 人工介入演示完成")

manual_review_demo()
