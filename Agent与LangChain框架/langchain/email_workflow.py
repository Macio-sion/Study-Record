from __future__ import annotations
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END, START
from typing import Annotated, TypedDict, Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, RetryPolicy
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig, ConfigurableField

class EmailAgentState(TypedDict):
    # 原始数据(输入)
    email_content: str
    sender_email: str
    email_id: str
    # 邮件类别state
    classification: EmailClassification | None  # 节点invoke的中间状态
    # 原始搜索(RAG) 可以是web、MIS、数据库
    search_result: list[str] | None
    # 该用户的历史问题
    customer_history: dict | None
    # 处理的结果数据(输出)
    draft_response: str | None
    messages: list[str] | None
    # messages: Annotation[[BaseMessage], add_messages]

class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str

model_name = "qwen2.5:7b-instruct-q4_K_M"

config = RunnableConfig(
    temperature=0.8,
    configurable={
        "thread_id": "01"
    }
)

model = ChatOllama(model=model_name)

def read_email(state: EmailAgentState) -> dict:
    """Extract and parse email content"""
    # 在生产环境中，这将连接到您的邮件服务
    print(f"邮件内容:{state.get("email_content")}")
    return {
        "messages": [HumanMessage(content=f"正在处理邮件: {state['email_content']}")]
    }

def classify_intent(state: EmailAgentState) -> Command[Literal["search_documentation", "human_review", "draft_response", "bug_tracking"]] | dict:
    """
    解析意图, 利用LLM对邮件的意图，紧急程度进行分类，根据分类结果路由到下一个节点
    """
    # 结构化输出节点
    structured_llm = model.with_structured_output(EmailClassification)  # 意图分类
    # 设置提示词，通常由专门的模板供引用
    classification_prompt = f"""
    分析此客户邮件，并进行分类:

    邮件内容: {state["email_content"]}
    发件人: {state["sender_email"]}

    请提供分类结果，包括意图、紧急程度、主题与摘要。
    """
    # 得到意图分类结果
    classification = structured_llm.invoke(classification_prompt)
    print(classification)
    # 根据分类路由
    if classification["intent"] == "billing" or classification["urgency"] == "critical":
        # 人工审核
        goto = "human_review"
    elif classification["intent"] in ["question", "feature"]:
        # 知识库检索
        goto = "search_documentation"
    elif classification["intent"] == "bug":
        # 处理节点
        goto = "bug_tracking"
    else:
        goto = "draft_response"
        
    return Command(
        update={
            "classification": classification
        },
        goto=goto
    )

def search_documentation(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """在知识库中搜索相关信息。"""
    # 根据分类结果构建搜索查询。
    classification = state.get('classification', {})
    query = f"{classification.get('intent', '')} {classification.get('topic', '')}"

    try:
        # 在此处实现您的搜索逻辑
        # 存储原始搜索结果，而非格式化文本
        search_results = [
            "通过“设置”>“安全”>“更改密码”来重置密码",
            "密码长度必须至少为12个字符",
            "需包含大写字母、小写字母、数字和符号",
        ]
    except Exception as e:
        # 对于可恢复的搜索错误，存储错误信息并继续执行。
        search_results = [f"搜索服务暂时不可用。: {str(e)}"]

    return Command(
        update={"search_results": search_results},  # 存储原始结果或错误信息。
        goto="draft_response"
    )

def bug_tracking(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """创建或更新缺陷追踪工单。"""

    # 在您的缺陷追踪系统中创建工单。
    ticket_id = "BUG-12345"  # 将通过 API 创建。

    return Command(
        update={
            "search_results": [f"缺陷工单 {ticket_id} 已创建。"],
            "current_step": "缺陷已追踪"
        },
        goto="draft_response"
    )

def draft_response(state: EmailAgentState) -> Command[Literal["human_review", "send_reply"]]:
    """利用上下文生成响应，并根据质量进行路由。"""

    classification = state.get('classification')
    print(classification)
    # 按需从原始状态数据中格式化上下文。
    context_sections = []

    if state.get('search_results'):
        # 为提示格式化搜索结果。
        formatted_docs = "\n".join([f"- {doc}" for doc in state['search_results']])
        context_sections.append(f"相关文档:\n{formatted_docs}")

    if state.get('customer_history'):
        # 为提示格式化客户数据。
        context_sections.append(f"客户等级: {state['customer_history'].get('tier', 'standard')}")

    # 使用格式化后的上下文构建提示。
    draft_prompt = f"""
    请草拟一封回复此客户邮件的信函：
    {state['email_content']}

    Email intent: {classification.get('intent', 'unknown')}
    Urgency level: {classification.get('urgency', 'medium')}

    {chr(10).join(context_sections)}   # char是换行（Line Feed:LF）

    指南：
    - 保持专业且乐于助人
    - 解决他们的具体问题
    - 在相关时使用提供的文档
    """

    response = model.invoke(draft_prompt)

    # 根据紧急程度和意图判断是否需要人工审核。
    needs_review = (
        classification.get('urgency') in ['high', 'critical'] or
        classification.get('intent') == 'complex'
    )

    # 路由至合适的下一个节点。
    goto = "human_review" if needs_review else "send_reply"

    return Command(
        update={"draft_response": response.content},  # 仅存储原始响应。
        goto=goto
    )

from langgraph.types import interrupt
def human_review(state: EmailAgentState) -> Command[Literal["send_reply", END]]:
    
    # 审核者审批的信息细节也需要设计
    """
    {
        "approved": True/False,
        "edited_response": "内容的修改",
        "advise": "意见与需求"
    }
    """
    human_decision = interrupt({  # 这里是程序的设计要点
        "email_id": state.get("email_id"),
        "original_email": state.get("email_content"),
        "draft_response": state.get("draft_response"),
        "urgency": state['classification'].get("urgency"),
        "intent": state['classification'].get("intent"),
        "action": "请审核批准/编辑回复内容",
    }) # 挂起

    if human_decision.get("approved", False):
        return Command(
            update={
                "draft_response": human_decision.get("edited_response", state.get("draft_response"))
            },
            goto="send_reply"
        )
    else:
        return Command(
            update={},
            goto=END
        )
    
def send_reply(state: EmailAgentState) -> dict:
    """发送邮件回复。"""
    # 与邮件服务集成。
    print(f"正在发送回复。: {state['draft_response'][:100]}...")
    return {}

workflow = StateGraph(EmailAgentState)

workflow.add_node("read_email", read_email)
workflow.add_node("classify_intent", classify_intent, retry_policy=RetryPolicy(max_attempts=3))
workflow.add_node("search_documentation", search_documentation, retry_policy=RetryPolicy(max_attempts=3))
workflow.add_node("bug_tracking", bug_tracking)
workflow.add_node("draft_response", draft_response)
workflow.add_node("human_review", human_review)
workflow.add_node("send_reply", send_reply)

workflow.set_entry_point("read_email")
workflow.add_edge("read_email", "classify_intent") # 由llm自动路由，不加条件边
workflow.add_edge("send_reply", END)

agent = workflow.compile(checkpointer=MemorySaver())

config = RunnableConfig(
    temperature=0.8,
    configurable={
        "thread_id": "01"
    }
)
initial_state = {
    "email_content": "我的订阅重复扣费了！情况紧急",
    "sender_email": "675817401@qq.com",
    "email_id": "email_1",
    "messages": []
}
result = agent.invoke(
    initial_state,
    config=config
)
print(f"请处理{result['__interrupt__']}")

human_response = Command(
    resume={
        "approved": True,
        "edited_response": "对于重复扣费，我们深表歉意。我已立即启动了退款流程……"
    }
)

# 恢复执行
final_result = agent.invoke(human_response, config)
print(f"邮件已成功发送！")