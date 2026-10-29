from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict, Literal
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig, ConfigurableField
from langgraph.types import interrupt

model_name = "qwen2.5:7b-instruct-q4_K_M"

config = RunnableConfig(
    configurable={
        "thread_id": "01"
    }
)

model = ChatOllama(model=model_name)

from langchain.tools import tool
@tool
def multiply(a: int, b: int) -> int:
    """将 `a` 和 `b` 相乘。

    参数:
        a: 第一个整型
        b: 第二个整型
    """
    return a * b

@tool
def add(a: int, b: int) -> int:
    """将 `a` 和 `b` 相加。

    参数:
        a: 第一个整型
        b: 第二个整型
    """
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """将 `a` 和 `b` 相除。

    参数:
        a: 第一个整型
        b: 第二个整型
    """
    return a / b

tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

def exec_tool_node(tool, tool_args: dict):
    func = tool
    return func.invoke(tool_args)

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
    is_toolcall: bool
    
    tool_names: list
    tool_params: list
    tool_ids: list
    tool_call_time: int
    # tool_result: list[dict]
    
    done: bool
    
    iteration: int
    llm_calls: int

    state_result: bool

def fail_deal(state: AgentState) -> dict:
    if state.get("done", False) and state.get("state_result", True):
        error_message = AIMessage(content="工具调用出现错误。")
        return {
            'messages': error_message
        }
    return {}

def LLM_node(state: AgentState) -> dict:
    llm_calls = state.get("llm_calls", 0)
    iteration = state.get("iteration", 0)
    messages = state.get("messages", [])
    outputs = model_with_tools.invoke(
        messages,
    )
    if outputs.tool_calls:
        tool_name_list = []
        tool_params_list = []
        tool_id_list = []
        for tool_call in outputs.tool_calls:
            tool_name_list.append(tool_call.get("name"))
            tool_params_list.append(tool_call.get("args"))
            tool_id_list.append(tool_call.get("id"))
        return {
            "messages": outputs,
            "llm_calls": llm_calls + 1,
            "is_toolcall": True,
            "tool_names": tool_name_list,
            "tool_params": tool_params_list,
            "tool_ids": tool_id_list,
            "iteration": iteration,
            "done": False,
        }
    else:
        if iteration < 3:
            return {
                "messages": [AIMessage(content="请继续回答用户的问题。")],
                "is_toolcall": False,
                "llm_calls": llm_calls + 1,
                "iteration": iteration + 1,
                "done": False
            }
        else:
            return {
                "messages": [AIMessage(content="抱歉，我无法完成这个任务。")],
                "done": True,
                "llm_calls": llm_calls + 1,
                "state_result": False,
                "is_toolcall": False,
                "iteration": iteration,
            }
        
def tool_call_node(state: AgentState) -> dict:
    tool_results = []
    # 工具处理逻辑自定义
    tool_call_time = 0
    # 获取最后一条消息中的工具调用
    last_message = state.get("messages", [])[-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {
            "messages": [ToolMessage(content="没有需要执行的工具", tool_call_id="")],
            "tool_call_time": state.get("tool_call_time", 0),
        }
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id")
        
        tool_func = tools_by_name.get(tool_name)
        if tool_func:
            try:
                result = tool_func.invoke(tool_args)
                tool_results.append(
                    ToolMessage(content=str(result), tool_call_id=tool_id)
                )
                tool_call_time += 1
            except Exception as e:
                tool_results.append(
                    ToolMessage(content=f"工具执行失败: {str(e)}", tool_call_id=tool_id)
                )
        else:
            tool_results.append(
                ToolMessage(content=f"未找到工具: {tool_name}", tool_call_id=tool_id)
            )
    
    return {
        "messages": tool_results,
        "tool_call_time": state.get("tool_call_time", 0) + tool_call_time,
        "is_toolcall": False,  
    }
    # for tool_call in state['messages'][-1].tool_calls:
    #     tool_name = tool_call["name"]
    #     tool_args = tool_call["args"]  # 这是一个字典
    #     tool_id = tool_call["id"]
        
    #     tool_func = tools_by_name.get(tool_name)
    #     if tool_func:
    #         result = tool_func.invoke(tool_args)
    #         tool_results.append(
    #             ToolMessage(content=str(result), tool_call_id=tool_id)
    #         )
    #         tool_call_time += 1
    # return {
    #     "messages": tool_results,
    #     "tool_call_time": state.get("tool_call_time", 0) + tool_call_time
    # }

def router(state: AgentState) -> Literal["TOOL", END]:
    if state.get("done", False):
        return END
    elif state.get("is_toolcall", False):
        return "TOOL"
    else:
        return END
    
memory = MemorySaver()
graph = StateGraph(AgentState)

graph.add_node("FAIL_DEAL", fail_deal)
graph.add_node("LLM", LLM_node)
graph.add_node("TOOL", tool_call_node)

graph.set_entry_point("FAIL_DEAL")
graph.add_edge("FAIL_DEAL", "LLM")
graph.add_conditional_edges("LLM", router, ["TOOL", END])
graph.add_edge("TOOL", "LLM")

app = graph.compile(checkpointer=memory)

messages = [HumanMessage(content="3 和 4相加，然后乘以5，除以4")]
messages = app.invoke({"messages": messages}, config=config)
for m in messages["messages"]:
    m.pretty_print()