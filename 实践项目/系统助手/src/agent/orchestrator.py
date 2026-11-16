"""LangGraph 多智能体编排器。

采用 Supervisor-Worker 模式构建状态图：
- Supervisor 节点负责意图识别与任务路由（纯分类，不绑定工具）
- 各 Worker 节点绑定专属工具集，完成实际系统操作
- GENERAL_CHAT 节点作为兜底，处理无法识别意图或纯粹闲聊

对外提供：
- ``run``：阻塞式调用，返回最终回复
- ``astream``：异步生成器，产出 (event_type, payload) 进度/结果事件
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from loguru import logger

from agent.agents.app_manager_agent import AppManagerAgent
from agent.agents.env_var_agent import EnvVarAgent
from agent.agents.knowledge_agent import KnowledgeAgent
from agent.agents.registry_agent import RegistryAgent
from agent.agents.system_info_agent import SystemInfoAgent
from agent.agents.terminal_agent import TerminalAgent
from agent.conversation import ConversationManager
from agent.supervisor import SupervisorAgent
from infrastructure.llm.gpu_manager import GPUManager
from infrastructure.llm.ollama_provider import OllamaProvider
from utils.constants import TaskType
from utils.signal_bus import SignalBus

# 确保所有工具组已注册，供 Worker Agent 在构造时绑定专属工具集
import tools  # noqa: F401

GENERAL_CHAT_PROMPT = (
    "你是一个友好的 Windows 系统助手。请用简洁的中文回答用户的提问，"
    "并在用户询问系统操作时给出安全、可行的建议。"
)


class OrchestratorState(TypedDict, total=False):
    """编排器状态。"""

    user_message: str
    history: List[BaseMessage]
    task_type: str
    reason: str
    final_response: str


class AgentOrchestrator:
    """多智能体编排器。"""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.signal_bus = SignalBus.instance()
        self.provider = OllamaProvider(config.llm)
        self.gpu_manager = GPUManager(
            self.provider,
            idle_timeout=self.provider.idle_timeout,
            signal_bus=self.signal_bus,
        )
        self.supervisor = SupervisorAgent(self.provider, config)
        self.conversation = ConversationManager(config)
        self.workers: Dict[TaskType, Any] = {
            TaskType.SYSTEM_INFO: SystemInfoAgent(self.provider, config),
            TaskType.APP_MANAGER: AppManagerAgent(self.provider, config),
            TaskType.TERMINAL: TerminalAgent(self.provider, config),
            TaskType.REGISTRY: RegistryAgent(self.provider, config),
            TaskType.ENV_VAR: EnvVarAgent(self.provider, config),
            TaskType.KNOWLEDGE_QA: KnowledgeAgent(self.provider, config),
        }
        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    # 图节点
    # ------------------------------------------------------------------
    def _supervisor_node(self, state: OrchestratorState) -> dict:
        result = self.supervisor.classify(
            state["user_message"],
            history=state.get("history"),
        )
        return {"task_type": result.task_type.value, "reason": result.reason}

    def _general_chat_node(self, state: OrchestratorState) -> dict:
        messages: List[BaseMessage] = [SystemMessage(content=GENERAL_CHAT_PROMPT)]
        if state.get("history"):
            messages.extend(state["history"])
        messages.append(HumanMessage(content=state["user_message"]))
        response = self.provider.get_chat_model().invoke(messages)
        return {"final_response": (response.content or "").strip()}

    def _make_worker_node(self, task_type: TaskType):
        worker = self.workers[task_type]

        def node(state: OrchestratorState) -> dict:
            context = f"任务类型: {task_type.value}; 路由原因: {state.get('reason', '')}"
            result = worker.invoke(state["user_message"], task_context=context)
            return {"final_response": result}

        return node

    # ------------------------------------------------------------------
    # 图构建
    # ------------------------------------------------------------------
    @staticmethod
    def _route(state: OrchestratorState) -> str:
        task_type = state.get("task_type", TaskType.GENERAL_CHAT.value)
        # 回收站工具绑定在 AppManagerAgent 上，路由至应用管理节点
        if task_type == TaskType.RECYCLE_BIN.value:
            return TaskType.APP_MANAGER.value
        if task_type in {
            TaskType.SYSTEM_INFO.value,
            TaskType.APP_MANAGER.value,
            TaskType.TERMINAL.value,
            TaskType.REGISTRY.value,
            TaskType.ENV_VAR.value,
            TaskType.KNOWLEDGE_QA.value,
        }:
            return task_type
        return "GENERAL_CHAT"

    def _build_graph(self):
        graph = StateGraph(OrchestratorState)

        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("GENERAL_CHAT", self._general_chat_node)
        for task_type in (
            TaskType.SYSTEM_INFO,
            TaskType.APP_MANAGER,
            TaskType.TERMINAL,
            TaskType.REGISTRY,
            TaskType.ENV_VAR,
            TaskType.KNOWLEDGE_QA,
        ):
            graph.add_node(task_type.value, self._make_worker_node(task_type))

        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._route,
            {
                TaskType.SYSTEM_INFO.value: TaskType.SYSTEM_INFO.value,
                TaskType.APP_MANAGER.value: TaskType.APP_MANAGER.value,
                TaskType.TERMINAL.value: TaskType.TERMINAL.value,
                TaskType.REGISTRY.value: TaskType.REGISTRY.value,
                TaskType.ENV_VAR.value: TaskType.ENV_VAR.value,
                TaskType.KNOWLEDGE_QA.value: TaskType.KNOWLEDGE_QA.value,
                "GENERAL_CHAT": "GENERAL_CHAT",
            },
        )
        for node_name in (
            TaskType.SYSTEM_INFO.value,
            TaskType.APP_MANAGER.value,
            TaskType.TERMINAL.value,
            TaskType.REGISTRY.value,
            TaskType.ENV_VAR.value,
            TaskType.KNOWLEDGE_QA.value,
            "GENERAL_CHAT",
        ):
            graph.add_edge(node_name, END)

        return graph.compile()

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def _input_state(self, user_message: str, history: Optional[List[BaseMessage]] = None) -> dict:
        return {
            "user_message": user_message,
            "history": history if history is not None else self.conversation.get_history(),
        }

    def run(
        self,
        user_message: str,
        history: Optional[List[BaseMessage]] = None,
    ) -> str:
        """阻塞式执行，返回最终回复。"""
        self.gpu_manager.on_request_start()
        try:
            result = self.graph.invoke(self._input_state(user_message, history))
            response = result.get("final_response") or "抱歉，我没有理解你的意思，换个说法试试？"
            self.conversation.add_user_message(user_message)
            self.conversation.add_assistant_message(response)
            return response
        finally:
            self.gpu_manager.on_request_end()

    async def astream(
        self,
        user_message: str,
        history: Optional[List[BaseMessage]] = None,
    ) -> AsyncIterator[Tuple[str, str]]:
        """异步执行，产出 ``(event_type, payload)`` 事件。

        event_type 可取：
        - ``status``：进度提示（如「正在分析意图」「已识别任务」）
        - ``response``：最终回答
        """
        self.gpu_manager.on_request_start()
        final_response = ""
        try:
            yield ("status", "正在分析你的意图...")
            async for chunk in self.graph.astream(
                self._input_state(user_message, history),
                stream_mode="updates",
            ):
                for node_name, update in chunk.items():
                    if node_name == "supervisor":
                        task_type = update.get("task_type", "")
                        yield ("status", f"已识别任务: {task_type}")
                    elif update and update.get("final_response"):
                        final_response = update["final_response"]
            if not final_response:
                final_response = "抱歉，我没有理解你的意思，换个说法试试？"
            self.conversation.add_user_message(user_message)
            self.conversation.add_assistant_message(final_response)
            yield ("response", final_response)
        finally:
            self.gpu_manager.on_request_end()

    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        """释放 GPU 显存（程序退出时调用）。"""
        logger.info("编排器关闭，释放 GPU 显存")
        self.provider.release_gpu()


__all__ = ["AgentOrchestrator", "OrchestratorState"]