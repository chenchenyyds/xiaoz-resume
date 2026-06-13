"""Prometheus 业务埋点

暴露 /metrics 端点,供 Prometheus 抓取。

埋点列表:
  业务计数:
    - xiaoz_orders_created_total{product}        订单创建数
    - xiaoz_orders_paid_total{product}           订单支付成功
    - xiaoz_orders_refunded_total{product}       订单退款
    - xiaoz_revenue_total                        总收入(分)
    - xiaoz_user_active_total                    活跃用户
    - xiaoz_sms_sent_total{status}               短信发送(success/fail)
    - xiaoz_rewrite_calls_total{feature}         改写调用
    - xiaoz_redeem_used_total                    兑换码使用
  时延直方图:
    - xiaoz_llm_duration_seconds{feature}        LLM 调用耗时
    - xiaoz_http_request_duration_seconds{path}  HTTP 请求
  Gauge:
    - xiaoz_point_balance_total{point_type}      积分余额分布
"""
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
)
from fastapi import Request
from fastapi.responses import Response
import time


# ---------- 业务 Counter ----------
orders_created = Counter(
    "xiaoz_orders_created_total",
    "订单创建数",
    ["product_code"],
)
orders_paid = Counter(
    "xiaoz_orders_paid_total",
    "订单支付成功数",
    ["product_code", "pay_channel"],
)
orders_refunded = Counter(
    "xiaoz_orders_refunded_total",
    "订单退款数",
    ["product_code", "reason"],
)
revenue_total = Counter(
    "xiaoz_revenue_total",
    "总收入(分)",
    ["product_code"],
)
user_active = Counter(
    "xiaoz_user_active_total",
    "活跃用户(任意操作 +1)",
)
sms_sent = Counter(
    "xiaoz_sms_sent_total",
    "短信发送数",
    ["status"],   # success / fail
)
rewrite_calls = Counter(
    "xiaoz_rewrite_calls_total",
    "改写调用数",
    ["feature"],  # partial_rewrite / full_rewrite / full_rewrite_with_jd
)
redeem_used = Counter(
    "xiaoz_redeem_used_total",
    "兑换码使用数",
    ["points_bucket"],  # 0-100 / 100-500 / 500+
)
llm_failures = Counter(
    "xiaoz_llm_calls_failed_total",
    "LLM 调用失败",
    ["model", "error_type"],
)

# ---------- 时延直方图 ----------
llm_duration = Histogram(
    "xiaoz_llm_duration_seconds",
    "LLM 调用耗时(秒)",
    ["feature", "model"],
    buckets=[0.5, 1, 2, 3, 5, 10, 20, 30, 60],
)
http_duration = Histogram(
    "xiaoz_http_request_duration_seconds",
    "HTTP 请求耗时",
    ["method", "path", "status"],
    buckets=[0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10],
)

# ---------- Gauge(系统状态)----------
point_balance_gauge = Gauge(
    "xiaoz_point_balance_total",
    "当前全平台积分余额(按类型)",
    ["point_type"],
)
build_info = Info("xiaoz_build", "小Z简历构建信息")


# ---------- FastAPI 集成 ----------
def metrics_endpoint(request: Request) -> Response:
    """/metrics 端点"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def http_metrics_middleware(request: Request, call_next):
    """HTTP 请求耗时埋点中间件"""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # 跳过 /metrics 自身(避免无限递归)
    if request.url.path != "/metrics":
        http_duration.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        ).observe(duration)

    return response


# ---------- 便捷调用函数 ----------
def record_order_created(product_code: str):
    orders_created.labels(product_code=product_code).inc()


def record_order_paid(product_code: str, pay_channel: str, amount_fen: int):
    orders_paid.labels(product_code=product_code, pay_channel=pay_channel).inc()
    revenue_total.labels(product_code=product_code).inc(amount_fen)


def record_order_refunded(product_code: str, reason: str):
    orders_refunded.labels(product_code=product_code, reason=reason).inc()


def record_user_active():
    user_active.inc()


def record_sms_sent(success: bool):
    sms_sent.labels(status="success" if success else "fail").inc()


def record_rewrite(feature: str):
    rewrite_calls.labels(feature=feature).inc()


def record_redeem(points: int):
    bucket = "0-100" if points < 100 else "100-500" if points < 500 else "500+"
    redeem_used.labels(points_bucket=bucket).inc()


def record_llm_call(feature: str, model: str, duration_sec: float):
    llm_duration.labels(feature=feature, model=model).observe(duration_sec)


def record_llm_failure(model: str, error_type: str):
    llm_failures.labels(model=model, error_type=error_type).inc()


def setup_build_info(version: str, env: str):
    build_info.info({"version": version, "env": env})
