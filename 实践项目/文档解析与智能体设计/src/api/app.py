"""FastAPI 应用装配：RAK 任务 API + 自定义业务/鉴权路由。

运行：``python -m uvicorn api.app:app --host 0.0.0.0 --port 8000``（需把项目根与 src 加入
sys.path，见根目录 run_api.py）。
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_agent_kit.api import create_app

from api.routers import auth, jobs, resumes, tasks, users
from config.setting import get_settings
from taskqueue.kits import QUEUE_NAME, kit, stream_config

settings = get_settings()
logger = logging.getLogger("resume_agent.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建表（幂等；数据库未就绪时仅告警，不阻断启动）
    try:
        from db.connection import init_schema

        init_schema()
    except Exception as e:  # noqa: BLE001
        logger.warning("数据库建表失败（可能未启动 PostgreSQL）：%s", e)
    yield


def build_app() -> FastAPI:
    app = create_app(
        kit=kit,
        stream_config=stream_config,
        prefix="rak",
        queue_name=QUEUE_NAME,
        title="简历智能体 API",
        description="简历解析 / 智能问答 / 生成与优化 / 用户中心",
        version="1.0.0",
        lifespan=lifespan,
    )

    # 跨域（前端 Vite 开发服务器）
    origins = settings.cors_origins
    allow_origins = ["*"] if origins.strip() == "*" else [o.strip() for o in origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 自定义业务路由
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(users.feedback_router)
    app.include_router(resumes.router)
    app.include_router(jobs.router)
    app.include_router(tasks.router)

    return app


app = build_app()
