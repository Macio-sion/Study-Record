from langchain.chat_models import init_chat_model
import asyncio

model_name = "ollama:qwen2.5:7b-instruct-q4_K_M"
model = init_chat_model(
    model=model_name,
    temperature=0.7,
)

async def model_task1():  # 函数前，for或if语句前，with、while和try语句前都可以使用async关键字
    print("task1 start")
    response = await model.ainvoke("什么是咕咕嘎嘎。")
    print("task1 response:", response)
    return response

async def model_task2():  # 函数前，for或if语句前，with、while和try语句前都可以使用async关键字
    print("task2 start")
    response = await model.ainvoke("什么是咕咕嘎嘎。")
    print("task2 response:", response)
    return response

async def concurrent_model_tasks():
    # 创建多个协程对象
    task1 = asyncio.create_task(model_task1())
    task2 = asyncio.create_task(model_task2())

    pending = [task1, task2]
    while pending and len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            result = task.result()
            print("Task completed with result:", result)

if __name__ == "__main__":
    asyncio.run(concurrent_model_tasks())