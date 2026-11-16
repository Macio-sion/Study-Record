"""GPU 显存管理。

基于空闲计时器实现「空闲超时自动释放 GPU 显存」：
- 请求开始时取消计时
- 请求结束（无活动请求）时启动空闲计时
- 超时后调用 Ollama 释放显存（keep_alive=0，模型文件保留）

> 说明：空闲计时使用 ``threading.Timer``（守护线程）而非 ``QTimer``，因为
> 编排器可能在后台工作线程中运行，Qt 定时器只能在其所属线程被启动。
"""

from __future__ import annotations

import threading
from typing import Optional

from loguru import logger

from utils.signal_bus import SignalBus


class GPUManager:
    """GPU 显存管理器。"""

    def __init__(
        self,
        provider,
        idle_timeout: int = 30,
        signal_bus: Optional[SignalBus] = None,
    ) -> None:
        self.provider = provider
        self.idle_timeout = idle_timeout
        self.signal_bus = signal_bus or SignalBus.instance()
        self._active_requests = 0
        self._lock = threading.Lock()
        self._idle_timer: Optional[threading.Timer] = None

    # ------------------------------------------------------------------
    def on_request_start(self) -> None:
        """请求开始，取消释放计时器。"""
        with self._lock:
            self._active_requests += 1
            self._cancel_timer()
        self.signal_bus.gpu_status_changed.emit(True, "推理中")

    def on_request_end(self) -> None:
        """请求结束，若已无活动请求则启动空闲计时器。"""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            if self._active_requests == 0:
                self._start_timer()
        self.signal_bus.gpu_status_changed.emit(True, "空闲（计时中）")

    # ------------------------------------------------------------------
    def _start_timer(self) -> None:
        self._cancel_timer()
        self._idle_timer = threading.Timer(self.idle_timeout, self._on_idle_timeout)
        self._idle_timer.daemon = True
        self._idle_timer.start()

    def _cancel_timer(self) -> None:
        if self._idle_timer is not None:
            self._idle_timer.cancel()
            self._idle_timer = None

    def _on_idle_timeout(self) -> None:
        """空闲超时，释放 GPU 显存。"""
        logger.info(f"GPU 空闲超过 {self.idle_timeout}s，释放显存")
        self.provider.release_gpu()
        self.signal_bus.gpu_status_changed.emit(False, "空闲")


__all__ = ["GPUManager"]