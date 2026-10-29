"""
数据库连接管理
使用 SQLAlchemy 2.0 异步引擎 + 连接池
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.model.base import Base  # noqa: F401 — 统一使用 model/base.py 中的 Base

# 创建异步引擎（charset 由 URL 参数控制，aiomysql 原生支持）
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DEBUG,
    pool_pre_ping=False,  # aiomysql 的 ping() 与 pymysql 接口不兼容
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI 依赖注入：获取数据库会话
    用法: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    用于启动时健康检查
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"数据库连接检查失败: {type(e).__name__}: {e}")
        return False
