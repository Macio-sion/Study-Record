"""全局信号总线。

提供跨模块通信的统一通道（单例 QObject）。所有模块通过 SignalBus 解耦，
UI 层、Agent 层、工具层、权限层之间的事件均经由本总线传递。
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """全局信号总线（单例）。"""

    _instance: "SignalBus | None" = None

    # UI -> Agent
    user_message_sent = Signal(str)

    # Agent -> UI
    token_streamed = Signal(str)          # 流式输出 token
    response_complete = Signal(str)       # 完整响应
    tool_executing = Signal(str)          # 工具执行中（显示进度）
    confirm_requested = Signal(str, str, int)  # action, description, risk_level
    confirm_result = Signal(bool)         # 用户确认结果

    # 系统状态
    memory_usage_updated = Signal(float)  # 内存占用 (MB)
    gpu_status_changed = Signal(bool, str)  # GPU 状态 (是否占用, 描述)
    llm_status_changed = Signal(bool, str)  # LLM/Ollama 状态 (是否可用, 描述)

    def __new__(cls) -> "SignalBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # QObject 需要在实例上初始化；new 返回后由 Python 调用 __init__
        return cls._instance

    def __init__(self) -> None:
        # 单例需保证 QObject 只初始化一次
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._initialized = True

    @classmethod
    def instance(cls) -> "SignalBus":
        """获取全局单例实例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


__all__ = ["SignalBus"]