import httpx
from httpx_sse import aconnect_sse
import asyncio
import json
import sys

BASE = "http://127.0.0.1:8000"

async def main() -> None:
    # 1) 提交任务（先入队、后消费，保证 SSE 客户端来得及订阅 token 流）
    submit = {
        "message": "请调用 get_company_info 工具，查询“Redis”公司位于哪个城市、主营业务是什么？"
    }

    # 2) 订阅任务结果（token 流）
    async with httpx.AsyncClient(timeout=180) as client:
        # 提交任务
        r = await client.post(F"{BASE}/tasks", json=submit)
        r.raise_for_status() # 检查请求是否成功
        task_id = r.json()["task_id"]
        print(f"任务ID: {task_id}")
    
    events: list[dict] = [] # 存储所有事件
    stop = asyncio.Event() # 用于停止订阅

    async def consume_sse() -> None:
        # 创建HTTPX客户端
        async with httpx.AsyncClient(timeout=None) as c:
            # 发起GET请求
            async with aconnect_sse(c, "GET", f"{BASE}/tasks/{tid}/stream") as sse:
                # 返回SSE生成器
                async for s in sse.aiter_sse():  # 这是异步生成器，每次返回一个事件，不阻塞主线程
                    # 处理返回的SSE的event与数据
                    print(s.data)
                    ev = {
                        "event": s.event, 
                        "data": s.data
                    }
                    events.append(ev)
                    # 事件结束、或者失败，或者取消都终止请求
                    if s.event in ("done", "failed", "cancelled"):
                        break
        stop.set() # 所有任务不再block阻塞

    # 创建任务
    consumer = asyncio.create_task(consume_sse())
    await asyncio.sleep(1)
    await asyncio.wait_for(stop.wait(), timeout=180)
    # 等待所有任务完成
    await consumer

    for ev in events:
        try:
            d = json.loads(ev["data"])
            body = d.get("message") or d.get("response") or d.get("detail") or d
        except Exception:
            body = ev["data"]
        print(f"  -> {ev['event']:<8} {str(body)[:120]}")

    # 4) 任务终态与结果核验
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{BASE}/tasks/{tid}")
        r.raise_for_status()
        st = r.json()
        print(f"\n[verify] status={st.get('status')} result={str(st.get('result'))[:200]}")