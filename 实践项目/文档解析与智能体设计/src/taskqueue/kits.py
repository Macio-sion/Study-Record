"""AgentKit 装配：把任务 handler 封装进 Redis 队列，供 API 提交与 worker 消费。

参考 `28_RedisAgentPipeline`/`发布` 下的实现：``AgentKit`` 负责 Redis 任务队列，
``tasks = [kit.worker_task]`` 交给 ``rak worker --tasks taskqueue.kits:tasks`` 后台消费。
"""

from __future__ import annotations

from config.setting import get_settings
from redis_agent_kit import AgentKit, StreamConfig
from redis_agent_kit.streaming import ChannelScope

from taskqueue.handlers import resume_agent_handler

settings = get_settings()

# 统一队列名：API 与 worker 保持一致（``rak worker --name resume-agent``）
QUEUE_NAME = "resume-agent"

# SSE 流式配置：任务级通道（前端可用 /tasks/{id}/stream 订阅进度）
stream_config = StreamConfig(
    enabled=True,
    channels={ChannelScope.TASK},
)

kit = AgentKit(
    redis_url=settings.redis_url,
    agent_callable=resume_agent_handler,
    queue_name=QUEUE_NAME,
    stream_config=stream_config,
    auto_result_middleware=True,
)

# 供 `rak worker --tasks taskqueue.kits:tasks` 消费的任务列表
tasks = [kit.worker_task]
