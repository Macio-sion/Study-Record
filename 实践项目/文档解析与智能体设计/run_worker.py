"""开发启动脚本：启动后台 worker，消费 Redis 任务队列。

用法：``python run_worker.py``
（等价于 ``rak worker --name resume-agent --tasks taskqueue.kits:tasks``）。
"""

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

# 项目根与 src 加入 sys.path，使 ``taskqueue.kits`` 可被 Docket 按模块路径导入
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from docket import Worker  # noqa: E402
from config.setting import get_settings  # noqa: E402
from taskqueue.kits import QUEUE_NAME  # noqa: E402

settings = get_settings()


async def main() -> None:
    print(f"[worker] queue={QUEUE_NAME} redis={settings.redis_url}")
    await Worker.run(
        docket_name=QUEUE_NAME,
        url=settings.redis_url,
        concurrency=4,
        redelivery_timeout=timedelta(minutes=5),
        tasks=["taskqueue.kits:tasks"],
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[worker] stopped.")
