"""测试用 LLM / Provider 假实现。"""

from __future__ import annotations

from langchain_core.messages import AIMessage


class FakeChatModel:
    """按序返回预设 AIMessage，支持 bind_tools 链式调用。"""

    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.bound_tools = None
        self.messages = []

    def bind_tools(self, tools):
        self.bound_tools = tools
        return self

    def invoke(self, messages):
        self.messages = list(messages)
        if not self.responses:
            return AIMessage(content="")
        return self.responses.pop(0)


class FakeProvider:
    """返回预设 FakeChatModel 的 Provider 替身。"""

    def __init__(self, chat_model=None) -> None:
        self._chat_model = chat_model or FakeChatModel([AIMessage(content="ok")])

    def get_chat_model(self, model_name=None):
        return self._chat_model


__all__ = ["FakeChatModel", "FakeProvider"]