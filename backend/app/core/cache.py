"""Redis 客户端 - 验证码、限频、会话"""
import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


# ---------- 业务 key 工具 ----------
def sms_send_key(phone: str) -> str:
    """同号 60 秒内只发 1 次"""
    return f"sms:send:{phone}"


def sms_code_key(phone: str) -> str:
    """验证码本身(开发模式存 redis,生产建议只入库)"""
    return f"sms:code:{phone}"


def rate_limit_key(user_id: int, action: str) -> str:
    return f"rl:{action}:{user_id}"


# ---------- 限频 ----------
def incr_with_ttl(key: str, ttl: int) -> int:
    """原子 incr,首次设 ttl,返回当前次数"""
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, ttl)
    return int(pipe.execute()[0])


def get_count(key: str) -> int:
    v = redis_client.get(key)
    return int(v) if v else 0
