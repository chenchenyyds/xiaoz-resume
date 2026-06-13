"""限频工具 - 基于 Redis"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.cache import rate_limit_key, incr_with_ttl, get_count
from app.core.database import get_db
from app.core.exceptions import BizException, BizCode
from app.services.config_service import get_config_int


def check_rate_limit(user_id: int, action: str, max_count: int, window_seconds: int = 3600):
    """通用限频检查,超过抛 RATE_LIMIT"""
    key = rate_limit_key(user_id, action)
    cur = incr_with_ttl(key, window_seconds)
    if cur > max_count:
        raise BizException(BizCode.RATE_LIMIT, f"{action} 超过频次限制({max_count}/{window_seconds//60 or 1}分钟)")


def get_user_redis_counter(user_id: int, action: str) -> int:
    return get_count(rate_limit_key(user_id, action))
