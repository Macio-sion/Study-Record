from langchain.chat_models import init_chat_model
import asyncio
import time

model_name = "ollama:qwen2.5:7b-instruct-q4_K_M"
model = init_chat_model(
    model=model_name,
    temperature=0.7,
)

async def model_task1():  # 函数前，for或if语句前，with、while和try语句前都可以使用async关键字
    print("task1 start")
    response = await model.ainvoke("什么是咕咕嘎嘎。")
    print("task1 response:", response)

async def model_task2():  # 函数前，for或if语句前，with、while和try语句前都可以使用async关键字
    print("task2 start")
    response = await model.ainvoke("什么是咕咕嘎嘎。")
    print("task2 response:", response)

async def main():
    # 创建多个协程对象
    task1 = asyncio.create_task(model_task1())
    task2 = asyncio.create_task(model_task2())

    result = await asyncio.gather(task1, task2)
    return "ALL done"

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"协程耗时: {end_time - start_time:.2f}秒")