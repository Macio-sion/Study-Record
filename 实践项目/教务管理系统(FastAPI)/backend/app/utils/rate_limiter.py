"""选课限流器（令牌桶算法 - Redis实现）"""
import time
from app.utils.redis_client import get_redis


def rate_limiter(key: str, max_requests: int = 50, window: int = 1) -> bool:
    """简单计数限流器：key在window秒内最多max_requests次"""
    r = get_redis()
    try:
        current = r.get(key)
        if current and int(current) >= max_requests:
            return False
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        pipe.execute()
        return True
    except Exception:
        return True  # Redis不可用时放行，避免服务中断
