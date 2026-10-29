"""
全局中间件
- CORS中间件
- 请求日志中间件
- 响应耗时中间件
"""
import time
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

logger = logging.getLogger("middleware")


def register_middlewares(app):
    """注册所有中间件"""

    # 1. CORS 跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发阶段允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. 请求耗时中间件
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        if process_time > 0.5:
            logger.warning(
                f"慢请求: {request.method} {request.url.path} [{process_time:.3f}s]"
            )
        return response
