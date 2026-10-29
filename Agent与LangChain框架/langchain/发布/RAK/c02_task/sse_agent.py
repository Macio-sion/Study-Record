from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from redis_agent_kit import AgentKit, StreamConfig, TaskContext
from redis_agent_kit.api import create_app

@tool
def get_company_info(name: str, runtime: ToolRuntime) -> str:
    """按公司名称查询其所在城市与主营业务。"""
    table = {
        "字节跳动": "北京 · 短视频与AI应用", 
        "Redis": "旧金山 · 开源数据库", 
        "OpenAI": "旧金山 · 大语言模型"}
    
    return table.get(name, f"未收录公司：{name}")

llm = init_chat_model(
    model="qwen3.5:0.8b", 
    model_provider="ollama",
    base_url="http://localhost:11434", 
    temperature=0
)

agent = create_agent(
    model=llm, 
    tools=[get_company_info], 
    system_prompt="你是简洁的中文助手，回答尽量简短。"
)

async def agent_handler(ctx: TaskContext) -> dict:
    """把 langchain 智能体的流式输出逐 token 封装成 SSE 事件发布。"""

    text: list[str] = []
    await ctx.emitter.emit("请求已入队，智能体开始处理……")
    async for ev in agent.astream_events(
        input={
            "messages": [
                {"role": "user", "content": ctx.message}
            ]
        }, 
        version="v2",
        config={
            "configuable": {
                "ctx": ctx
            }
        }
    ):
        event = ev["event"]
        if event == "on_chat_model_stream":
            token = ev["data"]["chunk"].content
            if token:
                await ctx.emitter.emit_token(token)
                text.append(token)
        elif event == "on_tool_start":
            await ctx.emitter.emit(f"调用工具 {ev['name']}", update_type="tool_call")
    
    return {"response": "".join(text)}

stream_config = StreamConfig(
    enabled=True
)

kit = AgentKit(
    redis_url="redis://localhost:6379", 
    agent_callable=agent_handler,
    stream_config=stream_config, 
    queue_name="sse-demo"                     # 队列名字，启动Worker的时候保持一致
)

app = create_app(
    kit=kit, 
    stream_config=stream_config, 
    title="Redis Agent Kit SSE Demo"
)

tasks = [kit.worker_task]  # 供 `rak worker --tasks app:tasks` 后台消费任务队列