"""开发启动脚本：启动 FastAPI 服务。

用法：``python run_api.py``（等价于 ``uvicorn api.app:app --port 8000``）。
"""

import sys
from pathlib import Path

# 项目根（config/prompts）与 src（state/services/llm/agent/api/db/taskqueue）都要在 sys.path
# vendor 为本地安装的 fastapi（沙盒禁止写 site-packages 时的兜底），需置于 site-packages 之前
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

import uvicorn  # noqa: E402


if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=False)
