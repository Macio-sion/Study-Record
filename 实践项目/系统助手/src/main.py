"""程序入口。

启动顺序：Config → Logger → 单实例检测 → App（Ollama 检测 → Agent → UI）→ 事件循环。

运行方式（项目根目录）：
    python src/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 确保 src 目录在 sys.path 中（支持从任意工作目录启动，例如 python src/main.py）
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from infrastructure.config.config_manager import ConfigManager  # noqa: E402
from infrastructure.logging.logger import setup_logger  # noqa: E402
from ui.app import SysAssistantApp  # noqa: E402


def main() -> int:
    # 1. 配置
    config = ConfigManager().load()

    # 2. 日志
    setup_logger(level="INFO")

    # 3. 应用（含 Ollama 检测、Agent 编排、UI）
    app = SysAssistantApp([sys.argv[0]], config)

    # 4. 单实例检测
    if not app.ensure_single_instance():
        print("Windows 系统小助手已在运行中。")
        return 0

    # 5. 生命周期：退出时释放 GPU、保存配置
    app.aboutToQuit.connect(app.shutdown)

    # 6. 初始化并进入事件循环
    app.initialize()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())