"""系统配置服务 - 业务参数运行时从 DB 读"""
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.config import SystemConfig


# 进程内缓存(配置很少变,V1 不上 Redis 缓存)
_cache: dict[str, str] = {}


def get_config(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    if key in _cache:
        return _cache[key]
    row = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    val = row.config_value if row else default
    if val is not None:
        _cache[key] = val
    return val


def get_config_int(db: Session, key: str, default: int = 0) -> int:
    v = get_config(db, key, str(default))
    try:
        return int(v) if v is not None else default
    except (ValueError, TypeError):
        return default


def get_config_float(db: Session, key: str, default: float = 0.0) -> float:
    v = get_config(db, key, str(default))
    try:
        return float(v) if v is not None else default
    except (ValueError, TypeError):
        return default


def refresh_cache():
    """清空缓存,后台改了配置后调用"""
    _cache.clear()
    logger.info("system_configs 缓存已清空")
