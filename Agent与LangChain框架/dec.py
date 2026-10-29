from langchain.agents.middleware import AgentMiddleware, before_agent, before_model, wrap_model_call, wrap_tool_call, AgentState, after_model, after_agent, ModelRequest, ModelResponse, ExtendedModelResponse
from langchain.messages import HumanMessage, ToolMessage
from typing import Any, Callable
from langgraph.types import Command
from langgraph.runtime import Runtime
from langchain.agents.middleware.types import StateT, ContextT, ResponseT
from loguru import logger
import time
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain.embeddings import init_embeddings, Embeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document


class LogRecord(AgentState):
    start_time: float
    end_time: float
    num_model_call: int
    token_inputs: int
    token_outputs: int
    model_usage_time: float
    token_list: list


@before_model
def log_before_model_call(state: LogRecord, runtime: Runtime[ContextT]):
    # Log the model call
    logger.info(f"Model call will started")
    return {
        "start_time": time.time()
    }

@wrap_model_call
def log_wrap_model_call(request, handler):
    logger.info(f"Model call started")
    response = handler(request)
    print("4.wrap_model_call")
    return response

@after_model
def log_after_model_call(state: LogRecord, runtime: Runtime[ContextT]):
    logger.info(f"Model call finished")
    return {
        "end_time": time.time(),
        "num_model_call": state.get("num_model_call", 0) + 1,
        "token_inputs": state["messages"][-1].usage_metadata.get("input_tokens"),
        "token_outputs": state["messages"][-1].usage_metadata.get("output_tokens"),
    }

@after_agent
def log_after_agent_call(state: LogRecord, runtime: Runtime[ContextT]):
    logger.info(f"Agent call finished")
    return {
        "model_usage_time": state.get("end_time", 0) - state.get("start_time", 0),
        "token_list": [state.get("token_inputs", 0), state.get("token_outputs", 0)],
    }

if __name__ == "__main__":
    from langchain.agents import create_agent

    middleware_list = [log_before_model_call, log_wrap_model_call, log_after_model_call, log_after_agent_call]

    agent = create_agent(
        model="ollama:qwen3.5:0.8b",
        tools=[],
        middleware=middleware_list,
        system_prompt="你是AI助手。",
        state_schema=LogRecord
    )

    outputs = agent.invoke(
        input={
            "messages": [
                HumanMessage(content="你好！")
            ]
        }
    )

    print(outputs)

