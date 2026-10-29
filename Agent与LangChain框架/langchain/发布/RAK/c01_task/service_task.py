from redis_agent_kit import AgentKit, EmitterMiddleware
from redis_agent_kit.api import create_app  # 封装了FastAPI的创建

from agent_task import langchain_agent

# 创建AgentKit实例
# rak:langchain_agent_queue 指的是Redis中存储队列的表名
agent_kit = AgentKit(
    redis_url="redis://127.0.0.1:6379",  # Redis连接地址,用来管理任务队列
    middleware=[EmitterMiddleware()],
    agent_callable=langchain_agent,  # 任务处理函数，队列处理的任务
    queue_name="langchain_agent_queue",
)

tasks = [agent_kit.worker_task]

app = create_app(kit=agent_kit)
