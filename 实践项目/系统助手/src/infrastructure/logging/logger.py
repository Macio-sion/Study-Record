"""日志系统。

基于 loguru 的全局日志配置，提供控制台 + 文件双输出，支持日志轮转与保留。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger(
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> "logger":
    """初始化全局日志。

    Args:
        log_dir: 日志输出目录，默认 data/logs
        level: 日志级别
        rotation: 单个日志文件大小阈值，超过后轮转
        retention: 日志保留时长
    """
    # 默认输出到项目根目录 data/logs（与 ConfigManager.DATA_DIR 保持一致）
    log_dir = Path(log_dir) if log_dir else (Path(__file__).resolve().parents[3] / "data" / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(sys.stderr, format=_LOG_FORMAT, level=level)
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format=_LOG_FORMAT,
        level=level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
    )

    logger.debug(f"日志系统已初始化，输出目录: {log_dir}")
    return logger


__all__ = ["setup_logger", "logger"]