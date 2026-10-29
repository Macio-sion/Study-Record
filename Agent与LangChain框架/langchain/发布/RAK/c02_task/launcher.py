# 使用httpx提交任务
import os
import subprocess
import httpx
from httpx_sse import aconnect_sse    # http支持SSE（Server Sent Event）
import time
import asyncio

process: list[subprocess.Popen] = []

def start(cmd: list[str], name: str):
    """
    启动一个子进程，执行指定的命令。
        uvicorn: ["python", "-m", "uvicorn", "sse_agent:app", "--port", "8000", "--log-level", "warning"]
        rak:[
            "rak", "worker",                              # 启动工作器
            "--name", "sse-demo",                         # Redis队列名，与代码中AgentKit指定的queue_name一致
            "--redis-url", "redis://127.0.0.1:6379",      # Redis服务器连接（可选））
            "--tasks", "sse_agent:tasks"                  # 任务名：模块：任务名
            ],
    """
    log = open(
        file=os.path.join(os.path.dirname(__file__), f"{name}.log"),
        mode="w",
        encoding="utf-8"
    )

    p = subprocess.Popen(
        args=cmd, 
        cwd="./",   
        stdout=log, 
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    process.append(p)

    return p

BASE = "http://127.0.0.1:8000"

async def wait_ready(timeout: float = 45.0) -> None:
    """
        验证Agent服务的是否健康

        Args
            timeout: 验证Agent服务是否正常启动
    """
    async with httpx.AsyncClient() as c:
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                r = await c.get(f"{BASE}/health")
                if r.status_code == 200 and r.json().get("status") == "healthy":
                    print("[已准备] API服务器已经正常运行。"); return
            except Exception:
                pass
            await asyncio.sleep(0.5)
    raise SystemExit("API服务器没有正常运行。")




# 启动服务
async def main() -> None:
    # 1) 启动 API 服务
    start(["python", "-m", "uvicorn", "sse_agent:app", "--port", "8000", "--log-level", "warning"], "uvicorn")
    # 检查服务是否健康
    await wait_ready()

    # 2）启动后台 worker，消费队列并触发智能体，Token 经 Pub/Sub -> SSE 推送
    start(
        [
            "rak", "worker",                              # 启动工作器
            "--name", "sse-demo",                         # Redis队列名，与代码中AgentKit指定的queue_name一致
            "--redis-url", "redis://127.0.0.1:6379",      # Redis服务器连接（可选））
            "--tasks", "sse_agent:tasks"                  # 任务名：模块：任务名
        ], 
        "worker"                                          # 进程名，也是日志文件名
    )
