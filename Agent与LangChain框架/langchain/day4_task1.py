from __future__ import annotations
from typing import Annotated, TypedDict, Literal
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.types import Command, interrupt
from langchain_core.runnables import RunnableConfig
import asyncio
from langgraph.runtime import Runtime

# ===== 父图状态 =====
class ResearchState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    summary: QueryAnalysis | None
    valid: bool
    search_results: str | None
    iteration: int
    max_iterations: int
    final_report: str | None
    status: Literal["work", "llm_fail", "search_fail"]
    phase: Literal["intent_retrie", "work_deal", "reporting"]

# ===== 子图状态 =====
class ExecQuery(TypedDict):
    summary: "QueryAnalysis"  # 接收父图传入的摘要
    contents: str | None
    search_results: str | None
    valid: bool
    status: Literal["work", "llm_fail"]
    messages: Annotated[list[BaseMessage], add_messages]

class QueryAnalysis(TypedDict):
    analysis: str
    search_plan: list[str]

# ===== 初始化模型 =====
model_name = "qwen3.5:0.8b"
model = ChatOllama(model=model_name)
def get_model_from_config(config: RunnableConfig) -> ChatOllama:
    """
    根据配置获取模型实例
    """
    model_name = config.get("configurable", {}).get("model_name", "qwen2.5:7b-instruct-q4_K_M")
    temperature = config.get("configurable", {}).get("temperature", 0.3)
    return ChatOllama(model=model_name, temperature=temperature)

# ============================================================
# 子图：负责执行搜索
# ============================================================

def query_format(state: ExecQuery, config: RunnableConfig) -> Command[Literal["search", END]]:
    """
    子图入口：根据 summary 生成搜索查询内容
    """
    # 修正：检查 summary 是否存在，而不是检查是否为空
    if state.get("summary") is None:
        return Command(
            update={
                "messages": [AIMessage(content="错误：未收到摘要信息")],
                "status": "llm_fail"
            },
            goto=END
        )
    
    digest = state["summary"]["analysis"]
    plan = state["summary"]["search_plan"]
    
    content_prompt = f"""
    根据以下摘要内容和搜索计划，生成一个搜索查询内容:

    摘要内容: {digest}
    搜索计划: 
    """
    for item in plan:
        content_prompt += f"- {item}\n"
    content_prompt += "\n请生成一个详细的搜索查询语句。"
    
    return Command(
        update={
            "messages": [AIMessage(content="📝 正在生成搜索查询...")],
            "status": "work",
            "contents": content_prompt
        },
        goto="search"
    )

async def search(state: ExecQuery, config: RunnableConfig) -> dict:
    """
    子图搜索节点：执行实际的搜索
    """
    if state.get("contents") is None:
        return {
            "valid": False,
            "status": "llm_fail",
            "messages": [AIMessage(content="❌ 搜索查询内容为空")]
        }
    model_name = config.get("configurable", {}).get("model_name", "qwen2.5:7b-instruct-q4_K_M")
    metadata = config.get("metadata", {})
    
    try:
        # 构造搜索提示
        search_prompt = f"请根据以下内容进行搜索，返回与搜索计划相关的结果：\n{state['contents']}"
        print(f"[config] model_name: {model_name}, metadata: {metadata}")
        result = model.ainvoke([HumanMessage(content=search_prompt)])
        result = await result  # 等待异步结果
    except Exception as e:
        print(f"模型访问错误: {e}")
        return {
            "status": "llm_fail",
            "valid": False,
            "messages": [AIMessage(content=f"❌ 模型调用失败: {e}")]
        }
    
    if not result.content or len(result.content.strip()) < 10:
        return {
            "valid": False,
            "status": "llm_fail",
            "messages": [AIMessage(content="❌ 搜索未返回有效结果")]
        }
    
    return {
        "messages": [AIMessage(content=f"🔍 搜索完成，获取到结果")],
        "valid": True,
        "search_results": result.content,
        "status": "work"
    }

# 构建子图
search_graph = StateGraph(ExecQuery)
search_graph.add_node("query_format", query_format)
search_graph.add_node("search", search)

search_graph.set_entry_point("query_format")
search_graph.add_edge("search", END)

# 子图独立编译（不带 checkpointer，共享父图的）
sub_app = search_graph.compile()

# ============================================================
# 父图：负责意图分析、流程控制
# ============================================================

async def intent_retrie(state: ResearchState, config: RunnableConfig) -> Command[Literal["work_deal", END]]:
    """
    父图入口：解析用户意图，生成摘要和搜索计划
    """
    print("[config] 当前执行配置: metadata 和 tags 已传入")
    # structured_llm = model.with_structured_output(QueryAnalysis)
    print("[intent_retrie] 将使用动态模型")
    print(f"model_name: {config.get('configurable', {}).get('model_name', 'qwen2.5:7b-instruct-q4_K_M')}")
    structured_llm = get_model_from_config(config=config).with_structured_output(QueryAnalysis)
    
    system_prompt = """
    你是一个意图分析专家。请解析用户的查询内容，将其转化为：
    1. analysis: 对查询内容的简要摘要（50字以内）
    2. search_plan: 与查询内容相关的3-5个搜索关键词或短语
    
    严格按以下JSON格式输出：
    {
        "analysis": "...",
        "search_plan": ["关键词1", "关键词2", ...]
    }
    """
    
    query_prompt = f"用户查询：{state['query']}\n请分析意图并生成搜索计划。"
    
    try:
        summary = await structured_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query_prompt)
        ])
    except Exception as e:
        print(f"模型访问错误: {e}")
        return Command(
            update={
                "messages": [AIMessage(content=f"❌ 意图分析失败: {e}")],
                "status": "llm_fail",
                "phase": "intent_retrie",
                "summary": None
            },
            goto=END
        )
    
    print(f"[意图分析] 成功解析: {summary}")
    
    return Command(
        update={
            "messages": [AIMessage(content=f"📋 已分析意图，计划搜索: {summary['search_plan']}")],
            "status": "work",
            "phase": "intent_retrie",
            "summary": summary,
            "iteration": 0,
            "max_iterations": len(summary["search_plan"])
        },
        goto="work_deal"
    )

async def async_log(state: ResearchState, config: RunnableConfig) -> dict:
    """异步日志记录节点"""
    print(f"[异步日志] 当前阶段: {state.get('phase')}")
    print(f"[异步日志] 用户查询: {state.get('query')}")
    print(f"[异步日志] metadata: {config.get('metadata', {})}")
    print(f"[异步日志] tags: {config.get('tags', [])}")
    # 模拟异步 I/O（如写入数据库）
    await asyncio.sleep(0.1)
    return {"messages": [AIMessage(content="📋 日志记录完成")]}

async def work_deal(state: ResearchState, config: RunnableConfig) -> dict:
    """
    父图工作节点：调用子图执行搜索
    """
    summary = state.get("summary")
    if summary is None:
        return {
            "status": "search_fail",
            "phase": "work_deal",
            "messages": [AIMessage(content="❌ 缺少摘要信息，无法搜索")]
        }
    
    # 构建子图输入
    sub_input = {
        "summary": summary,
        "contents": None,
        "search_results": None,
        "valid": False,
        "status": "work",
        "messages": state.get("messages", [])
    }
    
    try:
        # 调用子图
        result = sub_app.ainvoke(sub_input, config=config)
        result = await result  # 等待异步结果
    except Exception as e:
        print(f"子图执行错误: {e}")
        return {
            "status": "search_fail",
            "phase": "work_deal",
            "messages": state.get("messages", []) + [AIMessage(content=f"❌ 子图执行失败: {e}")]
        }
    
    # 检查子图执行结果
    if result.get("status") == "llm_fail":
        return {
            "status": "llm_fail",
            "phase": "work_deal",
            "messages": state.get("messages", []) + [AIMessage(content="❌ 搜索过程中的模型调用失败")]
        }
    
    if not result.get("valid", False):
        return {
            "status": "search_fail",
            "phase": "work_deal",
            "messages": state.get("messages", []) + [AIMessage(content="❌ 搜索未返回有效结果")]
        }
    
    # 更新父图状态
    return {
        "search_results": result.get("search_results"),
        "iteration": state.get("iteration", 0) + 1,
        "valid": result.get("valid", False),
        "status": "work",
        "phase": "work_deal",
        "messages": result.get("messages", [])
    }

# def reporting(state: ResearchState) -> Command[Literal["work_deal", END]]:
#     """
#     父图报告节点：生成最终报告（支持人工介入）
#     """
#     # 如果搜索结果无效
#     if state.get("valid") is False:
#         return Command(
#             update={
#                 "final_report": "❌ 搜索结果无效，无法生成报告。请检查查询或重试。",
#                 "phase": "reporting"
#             },
#             goto=END
#         )
    
#     # 人工介入：让用户确认搜索结果是否满意
#     user_inputs = interrupt({
#         "search_results": state.get("search_results", "无搜索结果"),
#         "iteration": state.get("iteration", 0),
#         "max_iterations": state.get("max_iterations", 3),
#         "action": "请确认搜索结果是否满意？输入 'yes' 继续，'no' 重新搜索。"
#     })
    
#     # 如果用户不满意，回到 work_deal 重新搜索
#     if user_inputs.get("approved") is False:
#         return Command(
#             update={
#                 "phase": "work_deal",
#                 "messages": state.get("messages", []) + [AIMessage(content="🔄 用户要求重新搜索")]
#             },
#             goto="work_deal"
#         )
    
#     # 生成最终报告
#     report = f"""
#     📄 最终研究报告
#     =================
    
#     查询主题：{state.get('query', '未知')}
#     搜索轮次：{state.get('iteration', 0)}
#     搜索结果摘要：
#     {state.get('search_results', '无结果')}
    
#     =================
#     报告生成完成。
#     """
    
#     return Command(
#         update={
#             "final_report": report,
#             "phase": "reporting",
#             "messages": state.get("messages", []) + [AIMessage(content="✅ 报告生成完成")]
#         },
#         goto=END
#     )

def reporting(state: ResearchState) -> dict:
    """
    父图报告节点：生成最终报告， 这是修改版，人工介入在router中（支持人工介入）
    """
    # 如果搜索结果无效
    if state.get("valid") is False:
        return {
            "final_report": "❌ 搜索结果无效，无法生成报告。请检查查询或重试。",
            "phase": "reporting"
        }
    
    # 生成最终报告
    report = f"""
    📄 最终研究报告
    =================
    
    查询主题：{state.get('query', '未知')}
    搜索轮次：{state.get('iteration', 0)}
    搜索结果摘要：
    {state.get('search_results', '无结果')}
    
    =================
    报告生成完成。
    """
    
    return {
        "final_report": report,
        "phase": "reporting",
        "messages": state.get("messages", []) + [AIMessage(content="✅ 报告生成完成")]
    }

def router(state: ResearchState) -> Literal["work_deal", END]:
    """
    """
    if state.get("valid") is False:
        return END
    # 人工介入：让用户确认搜索结果是否满意
    user_inputs = interrupt({
        "search_results": state.get("search_results", "无搜索结果"),
        "iteration": state.get("iteration", 0),
        "max_iterations": state.get("max_iterations", 3),
        "action": "请确认搜索结果是否满意？输入 'yes' 继续，'no' 重新搜索。"
    })
    if user_inputs.get("approved") is False:
        return "work_deal"
    return END



# ===== 构建父图 =====
parent_graph = StateGraph(ResearchState)

parent_graph.add_node("intent_retrie", intent_retrie)
parent_graph.add_node("work_deal", work_deal)
parent_graph.add_node("reporting", reporting)

parent_graph.set_entry_point("intent_retrie")

# 添加边
parent_graph.add_edge("intent_retrie", "work_deal")
# work_deal 没有固定的下一个节点，由 reporting 或条件边决定
parent_graph.add_edge("work_deal", "reporting")
# 修改成路由
parent_graph.add_conditional_edges("reporting", router, {"work_deal": "work_deal", END: END})

# 编译父图（带 checkpointer）
app = parent_graph.compile(checkpointer=MemorySaver())

async def main():
    # config = {"configurable": {"thread_id": "test_research"}}
    config = {
    "configurable": {
        "thread_id": "test_research",
        # 新增可配置参数（下一阶段会用）
        "model_name": "qwen2.5:7b-instruct-q4_K_M",
        "model_name2": "qwen3.5:0.8b",
        "max_iterations": 3,
        "temperature": 0.3
    },
    "metadata": {
        "user_id": "user_12345",
        "session_id": "session_abc",
        "source": "web_ui",
        "environment": "development"
    },
    "tags": ["research", "ai_medical", "v1.0"]
}
    # 模拟人工介入：当 interrupt 触发时，自动通过
    # 实际使用时，这里需要用户输入
    # 这里我们手动模拟一个通过
    
    result = app.ainvoke({
        "messages": [],
        "query": "人工智能在医疗领域的应用",
        "summary": None,
        "valid": False,
        "search_results": None,
        "iteration": 0,
        "max_iterations": 3,
        "final_report": None,
        "status": "work",
        "phase": "intent_retrie"
    }, config=config)

    result = await result # 等待异步结果
    
    print("===== 中断内容显示 =====")
    print(f"中断内容: {result.get('__interrupt__', '无中断')}")

    human_review = Command(
        resume={
            "approved": True
        }
    )

    result = await app.ainvoke(human_review, config=config)
    print(f"final_result: {result.get('final_report')}")
    print("\n===================")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())