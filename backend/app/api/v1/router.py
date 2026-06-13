"""V1 API 路由聚合 - 22 + 6 = 28 个 API"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    user,
    files,
    rewrite,
    products,
    orders,
    redeem,
    withdraw,
)
from app.api.v1.admin import (
    dashboard,
    orders as admin_orders,
    codes,
    users,
    points,
    logs,
)

api_router = APIRouter()

# 用户端 13 个
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(files.router)
api_router.include_router(rewrite.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(redeem.router)
api_router.include_router(withdraw.router)

# 后台 15 个(原 9 + 新 6:积分流水 3 + 操作日志 2)
api_router.include_router(dashboard.router, prefix="/admin")
api_router.include_router(admin_orders.router, prefix="/admin")
api_router.include_router(codes.router, prefix="/admin")
api_router.include_router(users.router, prefix="/admin")
api_router.include_router(points.router, prefix="/admin")
api_router.include_router(logs.router, prefix="/admin")
