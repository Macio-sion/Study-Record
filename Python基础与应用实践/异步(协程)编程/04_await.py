"""
协程的简洁调用方式
"""
import asyncio
import time
import requests

async def download(task_name: str, id: int):
    # time.sleep(1)
    await asyncio.sleep(1)  # 模拟耗时操作
    response = requests.get("http://www.baidu.com")
    if response.status_code == 200:
        print(f"获取成功，{task_name}, 第{id}次")
    else:
        print(f"获取失败，{task_name}, 第{id}次")

NUM = 10
async def call_download(task_name: str):
    for i in range(NUM):
        await download(task_name, i)
    return f"{task_name}done"

async def main():
    # 创建多个协程对象
    task1 = asyncio.create_task(call_download("task1"))
    task2 = asyncio.create_task(call_download("task2"))

    result = await asyncio.gather(task1, task2)
    return "ALL done"

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"协程耗时: {end_time - start_time:.2f}秒")