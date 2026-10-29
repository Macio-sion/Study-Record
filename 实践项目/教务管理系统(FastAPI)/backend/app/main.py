"""
FastAPI 应用入口
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import check_db_connection
from app.common.middleware import register_middlewares
from app.common.exception import register_exception_handlers
from app.router.auth_router import auth_router
from app.router.user_router import user_router
from app.router.college_router import router as college_router
from app.router.student_router import router as student_router
from app.router.course_router import router as course_router
from app.router.teacher_router import teacher_router
from app.router.classroom_router import classroom_router
from app.router.schedule_router import schedule_router
from app.router.selection_router import selection_router
from app.router.attendance_router import attendance_router
from app.router.timetable_router import timetable_router
from app.router.score_router import score_router
from app.router.assignment_router import assignment_router
from app.router.leave_router import leave_router
from app.router.alert_router import alert_router
from app.router.club_router import club_router
from app.router.notice_router import notice_router
from app.router.log_router import log_router
from app.router.dashboard_router import router as dashboard_router
from app.router.notification_router import notification_router

# 确保日志目录存在
os.makedirs(settings.LOG_DIR, exist_ok=True)

# 日志配置
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(settings.LOG_DIR, "app.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 检查数据库连接
    db_ok = await check_db_connection()
    if db_ok:
        logger.info("数据库连接成功")
    else:
        logger.warning("数据库连接失败，请检查MySQL服务是否启动及配置是否正确")

    logger.info(f"应用已就绪，访问 http://localhost:8000/docs 查看API文档")
    yield
    # 关闭时
    logger.info(f"{settings.APP_NAME} 已关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="企业级教务管理系统 API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 注册中间件（CORS、请求耗时）
register_middlewares(app)

# 注册全局异常处理器
register_exception_handlers(app)

# 注册路由
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(college_router)
app.include_router(student_router)
app.include_router(classroom_router)
app.include_router(teacher_router)
app.include_router(course_router)
app.include_router(attendance_router)
app.include_router(schedule_router)
app.include_router(selection_router)
app.include_router(timetable_router)
app.include_router(score_router)
app.include_router(assignment_router)
app.include_router(leave_router)
app.include_router(alert_router)
app.include_router(club_router)
app.include_router(notice_router)
app.include_router(log_router)
app.include_router(dashboard_router)
app.include_router(notification_router)


@app.get("/", tags=["Health"])
async def root():
    """健康检查接口"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """详细健康检查"""
    db_ok = await check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": settings.APP_VERSION,
    }
