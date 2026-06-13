"""小Z简历后端 - FastAPI 主入口

V1 商业化 MVP:9 张表 + 用户端 13 API + 后台 9 API
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import BizException
from app.core import metrics
from app.api.v1.router import api_router


# ---------- loguru 接管 logging ----------
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子"""
    logger.info(f"🚀 {settings.APP_NAME} 启动,env={settings.APP_ENV}")
    metrics.setup_build_info(version="1.0.0", env=settings.APP_ENV)
    # 启动时建表（生产用 Alembic,这里先 auto-create 方便开发）
    init_db()
    yield
    logger.info(f"👋 {settings.APP_NAME} 关闭")


app = FastAPI(
    title="小Z简历 API",
    description="V1 商业化 MVP - 9 张表 + 22 个 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
)

# ---------- Prometheus 业务埋点中间件 ----------
app.middleware("http")(metrics.http_metrics_middleware)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 业务异常统一处理 ----------
@app.exception_handler(BizException)
async def biz_exception_handler(request: Request, exc: BizException):
    return JSONResponse(
        status_code=200,  # 业务异常 HTTP=200,业务码区分
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data,
        },
    )


# ---------- 路由 ----------
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV, "app": settings.APP_NAME}


# ---------- V1 体验版:用户端单页 ----------
@app.get("/", include_in_schema=False)
async def user_demo():
    """V1 体验版 - 用户端单页 SPA"""
    from fastapi.responses import FileResponse
    import os
    demo_path = os.path.join(os.path.dirname(__file__), "..", "user_demo.html")
    demo_path = os.path.abspath(demo_path)
    if os.path.exists(demo_path):
        return FileResponse(demo_path, media_type="text/html")
    return {"message": "user demo not found"}


@app.get("/admin", include_in_schema=False)
async def admin_demo():
    """V1 体验版 - 后台管理单页 SPA"""
    from fastapi.responses import FileResponse
    import os
    demo_path = os.path.join(os.path.dirname(__file__), "..", "admin_demo.html")
    demo_path = os.path.abspath(demo_path)
    if os.path.exists(demo_path):
        return FileResponse(demo_path, media_type="text/html")
    return {"message": "admin demo not found"}


# ---------- Prometheus 抓取端点 ----------
@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    """Prometheus 抓取端点,无需鉴权(但生产应限制内网)"""
    return metrics.metrics_endpoint(None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.APP_DEBUG)
