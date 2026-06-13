"""限流分级中间件

按用户类型(试用/付费/VIP)+ 端点类型(改写/支付/通用)分级限流。

注意:本模块与 app/core/rate_limit.py(简单 Redis 计数器限流)互补。
本模块提供基于用户等级的差异化限流。
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

from app.core.cache import redis_client
from app.core.security import get_current_user_optional


# ---------- 限流规则(从 system_configs 读,这里给默认值)----------
DEFAULT_RULES = {
    # (tier, endpoint_category) -> (count, window_seconds)
    ("trial", "rewrite_partial"): (10, 3600),  # 试用用户:部分改写 10/h
    ("trial", "rewrite_full"): (3, 3600),  # 试用用户:完整改写 3/h
    ("trial", "upload"): (5, 86400),  # 试用用户:上传 5/天
    ("trial", "general"): (60, 60),  # 试用用户:通用 60/min
    ("paid", "rewrite_partial"): (50, 3600),  # 付费用户:部分改写 50/h
    ("paid", "rewrite_full"): (15, 3600),  # 付费用户:完整改写 15/h
    ("paid", "upload"): (50, 86400),  # 付费用户:上传 50/天
    ("paid", "general"): (300, 60),  # 付费用户:通用 300/min
    ("vip", "rewrite_partial"): (200, 3600),  # VIP: 部分改写 200/h
    ("vip", "rewrite_full"): (60, 3600),  # VIP: 完整改写 60/h
    ("vip", "upload"): (200, 86400),  # VIP: 上传 200/天
    ("vip", "general"): (1000, 60),  # VIP: 通用 1000/min
    ("admin", "general"): (10000, 60),  # 管理员不限流
    ("anonymous", "general"): (30, 60),  # 匿名(未登录): 30/min
}


def classify_endpoint(path: str) -> str:
    """根据路径分类端点类型"""
    if "/rewrite/partial" in path:
        return "rewrite_partial"
    if "/rewrite/full" in path:
        return "rewrite_full"
    if "/files/upload" in path:
        return "upload"
    if "/admin/" in path:
        return "admin_general"
    return "general"


def get_user_tier(user_id: int = None) -> str:
    """判断用户等级(简化:V1 只有 trial/paid/admin)
    - 未登录: anonymous
    - 是管理员: admin
    - 有点积分且有过付费订单: paid
    - 否则: trial
    """
    if user_id is None:
        return "anonymous"
    # 真实判断应从 DB 查,这里给简化逻辑
    return "trial"


def check_rate_limit(tier: str, endpoint: str) -> tuple:
    """返回 (allowed, remaining, reset_at)"""
    key = (tier, endpoint)
    rule = DEFAULT_RULES.get(key, (60, 60))
    if tier == "admin":  # 管理员不限流
        return (True, 9999, 0)
    return (True, rule[0], rule[1])


class TieredRateLimitMiddleware(BaseHTTPMiddleware):
    """分级限流中间件

    使用方法:app.add_middleware(TieredRateLimitMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        # 跳过 /metrics 和 /health(避免被自己限流)
        if request.url.path in ("/metrics", "/health", "/docs", "/openapi.json"):
            return await call_next(request)

        # 提取用户(可选,不强制登录)
        user = None
        try:
            user = await get_current_user_optional(request)
        except Exception:
            pass

        user_id = user.id if user else None
        tier = (
            "admin"
            if (user and getattr(user, "is_admin", False))
            else get_user_tier(user_id)
        )
        endpoint = classify_endpoint(request.url.path)

        # 应用限流
        allowed, count, window = check_rate_limit(tier, endpoint)
        if not allowed:
            return JSONResponse(
                status_code=200,
                content={
                    "code": 42901,
                    "message": f"操作太频繁,请稍后再试",
                    "data": {
                        "tier": tier,
                        "endpoint": endpoint,
                        "limit": count,
                        "window": window,
                    },
                },
            )

        # Redis 计数器(原子)
        if user_id:
            key = f"rate:{tier}:{endpoint}:{user_id}:{int(time.time() / window)}"
        else:
            key = f"rate:{tier}:{endpoint}:{request.client.host if request.client else 'unknown'}:{int(time.time() / window)}"

        try:
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, window)
            if current > count:
                ttl = redis_client.ttl(key)
                return JSONResponse(
                    status_code=200,
                    content={
                        "code": 42901,
                        "message": f"操作太频繁,{ttl}秒后可重试",
                        "data": {
                            "tier": tier,
                            "endpoint": endpoint,
                            "retry_after": ttl,
                        },
                    },
                )
        except Exception:
            # Redis 挂了不阻塞业务
            pass

        response = await call_next(request)
        return response
