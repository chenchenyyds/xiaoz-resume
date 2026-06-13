"""
小Z简历 - Locust 压测脚本
================================
模拟 4 类用户行为:
  - anonymous: 匿名访问(浏览商品、注册)
  - trial:     试用用户(已有少量积分,会尝试改写)
  - paid:      付费用户(积分充裕,高频改写)
  - vip:       VIP 用户(高频 + 大文件)

覆盖 6 个核心 API:
  1. POST /auth/send-sms   发送验证码
  2. POST /auth/login      登录/注册
  3. POST /files/upload    上传简历
  4. POST /rewrite/partial 部分改写
  5. POST /rewrite/full    完整改写
  6. POST /orders          创建订单

阶梯加压(由命令行控制):
  locust -f locustfile.py --users 10  --spawn-rate 2  --run-time 60s  Headless
  locust -f locustfile.py --users 50  --spawn-rate 10 --run-time 120s Headless
  locust -f locustfile.py --users 100 --spawn-rate 20 --run-time 300s Headless
  locust -f locustfile.py --users 200 --spawn-rate 30 --run-time 600s Headless

报告输出:
  - HTML 报告:reports/loadtest_<timestamp>.html
  - JSON 报告:reports/loadtest_<timestamp>_stats.json
  - CSV 报告: reports/loadtest_<timestamp>_stats.csv / _failures.csv

使用方法:
  pip install -r requirements.txt
  locust -f locustfile.py --host=http://localhost:8000
"""
import os
import json
import time
import random
import string
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from locust import (
    HttpUser,
    task,
    between,
    events,
    LoadTestShape,
    constant,
    constant_pacing,
)

logger = logging.getLogger(__name__)

# ============================================================
# 全局配置
# ============================================================
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# 测试用户池(模拟真实手机号池)
PHONE_POOL = [
    f"138{random.randint(10000000, 99999999):08d}" for _ in range(100)
]
SMS_CODE = "123456"  # 开发模式固定验证码

# 改写测试原文(模拟用户输入)
SAMPLE_RESUMES = [
    """张三 | 男 | 25 岁 | 北京
工作经历:
2020.07 - 至今  某某科技有限公司  后端开发工程师
- 负责公司核心业务系统的开发和维护
- 参与过 3 个大型项目
- 写过一些代码

教育经历:
2016.09 - 2020.07  某某大学  计算机科学与技术  本科""",
    """李四 | 女 | 23 岁 | 上海
项目经验:
校园二手交易平台(2022.03-2022.06)
- 使用 Python + Django 开发
- 实现了用户注册、商品发布功能
- 数据库用 MySQL

个人评价:
性格开朗,学习能力强,能吃苦耐劳。""",
    """王五 | 男 | 28 岁 | 深圳
技能清单:
- Java / Spring Boot 3 年经验
- MySQL / Redis 熟悉
- 了解 Docker, Kubernetes

期望职位:高级 Java 开发""",
]

# JD 样本(用于含 JD 改写)
SAMPLE_JDS = [
    """职位:Python 后端开发工程师
要求:
1. 本科及以上学历,计算机相关专业
2. 3 年以上 Python 开发经验
3. 熟悉 Django / FastAPI
4. 熟悉 MySQL, Redis, 消息队列
5. 有高并发经验者优先""",
    """职位:Java 高级开发
要求:
1. 5 年以上 Java 经验
2. 精通 Spring Boot, MyBatis
3. 熟悉微服务架构
4. 有电商 / 金融项目经验优先""",
]


# ============================================================
# 公共工具
# ============================================================
def random_phone() -> str:
    """从手机号池随机取一个"""
    return random.choice(PHONE_POOL)


def random_text(min_len: int = 50, max_len: int = 500) -> str:
    """生成指定长度的随机文本(模拟简历片段)"""
    base = random.choice(SAMPLE_RESUMES)
    # 重复拼接至指定长度
    while len(base) < min_len:
        base += "\n" + random.choice(SAMPLE_RESUMES)
    return base[:max_len]


def random_jd() -> str:
    """随机 JD"""
    return random.choice(SAMPLE_JDS)


# ============================================================
# 用户类型 1: 匿名用户
# ============================================================
class AnonymousUser(HttpUser):
    """匿名访问:浏览商品、注册"""
    weight = 3
    wait_time = between(1, 3)

    def on_start(self):
        """模拟首次访问"""
        self.client.get("/health", name="[anon] health")

    @task(8)
    def view_products(self):
        """浏览商品列表(高频)"""
        with self.client.get(
            "/api/v1/products",
            name="[anon] GET /products",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and resp.json().get("code") == 0:
                resp.success()
            else:
                resp.failure(f"unexpected: {resp.status_code} {resp.text[:200]}")

    @task(2)
    def send_sms(self):
        """发送验证码(注册第一步)"""
        phone = random_phone()
        with self.client.post(
            "/api/v1/auth/send-sms",
            json={"phone": phone},
            name="[anon] POST /auth/send-sms",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 200 and "RATE_LIMIT" in resp.text:
                # 限流也算"成功",因为服务端正确处理
                resp.success()
            else:
                resp.failure(f"send-sms failed: {resp.text[:200]}")

    @task(1)
    def register_or_login(self):
        """注册/登录(模拟一次性行为)"""
        phone = random_phone()
        with self.client.post(
            "/api/v1/auth/login",
            json={"phone": phone, "code": SMS_CODE},
            name="[anon] POST /auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if data.get("token"):
                    resp.success()
                else:
                    resp.failure("no token in response")
            else:
                resp.failure(f"login failed: {resp.text[:200]}")


# ============================================================
# 用户类型 2: 试用用户
# ============================================================
class TrialUser(HttpUser):
    """试用用户:积分有限,中频改写"""
    weight = 4
    wait_time = between(2, 5)

    def on_start(self):
        """注册 + 登录获取 token"""
        self.phone = random_phone()
        self.token: Optional[str] = None
        self.headers = {"Authorization": ""}

        # 跳过 send-sms(开发环境验证码固定 123456)
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"phone": self.phone, "code": SMS_CODE},
            name="[trial] on_start login",
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self.token = data.get("token")
            self.headers["Authorization"] = f"Bearer {self.token}"
            logger.info(f"[trial] {self.phone} logged in")
        else:
            logger.warning(f"[trial] {self.phone} login failed: {resp.text[:100]}")

    @task(5)
    def view_me(self):
        """查看个人信息(高频)"""
        if not self.token:
            return
        self.client.get(
            "/api/v1/user/me",
            headers=self.headers,
            name="[trial] GET /user/me",
        )

    @task(3)
    def partial_rewrite(self):
        """部分改写(50 积分/次)"""
        if not self.token:
            return
        self.client.post(
            "/api/v1/rewrite/partial",
            json={
                "text": random_text(100, 300),
                "title": "工作经历",
                "style_hint": random.choice(["更专业", "更简洁", "更口语化", None]),
            },
            headers=self.headers,
            name="[trial] POST /rewrite/partial",
            timeout=30,
        )

    @task(1)
    def full_rewrite(self):
        """完整改写(1000 积分/次)"""
        if not self.token:
            return
        # V1 简化:不实际传 file_id,只测试接口形态
        self.client.post(
            "/api/v1/rewrite/full",
            json={
                "file_id": random.randint(1, 100),
                "style_hint": "突出技术深度",
            },
            headers=self.headers,
            name="[trial] POST /rewrite/full",
            timeout=60,
        )

    @task(2)
    def upload_resume(self):
        """上传简历(docx)"""
        if not self.token:
            return
        # 构造一个最小的 docx(实际压测可使用预生成的小文件)
        files = {
            "file": (
                "test_resume.docx",
                b"PK\x03\x04" + b"\x00" * 100,  # 假的 docx 内容
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        data = {"title": "我的简历"}
        self.client.post(
            "/api/v1/files/upload",
            files=files,
            data=data,
            headers=self.headers,
            name="[trial] POST /files/upload",
            timeout=15,
        )


# ============================================================
# 用户类型 3: 付费用户
# ============================================================
class PaidUser(HttpUser):
    """付费用户:积分充裕,高频改写 + 查看商品"""
    weight = 2
    wait_time = between(1, 3)

    def on_start(self):
        self.phone = random_phone()
        self.token: Optional[str] = None
        self.headers = {"Authorization": ""}

        resp = self.client.post(
            "/api/v1/auth/login",
            json={"phone": self.phone, "code": SMS_CODE},
            name="[paid] on_start login",
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self.token = data.get("token")
            self.headers["Authorization"] = f"Bearer {self.token}"

    @task(10)
    def partial_rewrite_high_freq(self):
        """部分改写(高频)"""
        if not self.token:
            return
        self.client.post(
            "/api/v1/rewrite/partial",
            json={"text": random_text(200, 800), "title": "项目经验"},
            headers=self.headers,
            name="[paid] POST /rewrite/partial",
            timeout=30,
        )

    @task(5)
    def full_rewrite_with_jd(self):
        """含 JD 的完整改写(1500 积分)"""
        if not self.token:
            return
        self.client.post(
            "/api/v1/rewrite/full",
            json={
                "file_id": random.randint(1, 100),
                "jd_text": random_jd(),
                "style_hint": "突出与 JD 的匹配",
            },
            headers=self.headers,
            name="[paid] POST /rewrite/full(with JD)",
            timeout=60,
        )

    @task(2)
    def create_order(self):
        """创建订单(模拟付费)"""
        if not self.token:
            return
        self.client.post(
            "/api/v1/orders",
            json={"product_code": random.choice(["single", "monthly", "points_1000"])},
            headers=self.headers,
            name="[paid] POST /orders",
        )

    @task(2)
    def upload_resume(self):
        if not self.token:
            return
        files = {
            "file": (
                "resume.docx",
                b"PK\x03\x04" + b"\x00" * 1024,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        self.client.post(
            "/api/v1/files/upload",
            files=files,
            headers=self.headers,
            name="[paid] POST /files/upload",
            timeout=15,
        )


# ============================================================
# 用户类型 4: VIP 用户
# ============================================================
class VIPUser(HttpUser):
    """VIP 用户:极限压力测试,模拟大文件 + 高频改写"""
    weight = 1
    wait_time = constant_pacing(1)  # 严格 1 秒 1 次

    def on_start(self):
        self.phone = random_phone()
        self.token: Optional[str] = None
        self.headers = {"Authorization": ""}

        resp = self.client.post(
            "/api/v1/auth/login",
            json={"phone": self.phone, "code": SMS_CODE},
            name="[vip] on_start login",
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self.token = data.get("token")
            self.headers["Authorization"] = f"Bearer {self.token}"

    @task(20)
    def spam_partial_rewrite(self):
        if not self.token:
            return
        self.client.post(
            "/api/v1/rewrite/partial",
            json={"text": random_text(500, 2000), "title": "高频改写测试"},
            headers=self.headers,
            name="[vip] POST /rewrite/partial(burst)",
            timeout=30,
        )

    @task(5)
    def full_rewrite_stress(self):
        if not self.token:
            return
        self.client.post(
            "/api/v1/rewrite/full",
            json={"file_id": random.randint(1, 1000), "jd_text": random_jd()},
            headers=self.headers,
            name="[vip] POST /rewrite/full(stress)",
            timeout=60,
        )


# ============================================================
# 阶梯加压曲线(LoadTestShape)
# ============================================================
class StepLoadShape(LoadTestShape):
    """
    阶梯加压: 10 → 50 → 100 → 200 用户
    每阶段 60 秒
    """
    stages = [
        {"duration": 60,  "users": 10,  "spawn_rate": 2},   # 预热
        {"duration": 120, "users": 50,  "spawn_rate": 5},   # 50 并发
        {"duration": 180, "users": 100, "spawn_rate": 10},  # 100 并发
        {"duration": 240, "users": 200, "spawn_rate": 20},  # 200 并发
        {"duration": 300, "users": 50,  "spawn_rate": 50},  # 降压
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None  # 结束


# ============================================================
# 报告自定义 + 事件钩子
# ============================================================
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """压测开始时记录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    environment.run_id = timestamp
    logger.info(f"🚀 Load test started: {timestamp}")
    logger.info(f"   Target host: {environment.host}")
    logger.info(f"   Report dir:  {REPORT_DIR.absolute()}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """压测结束时输出报告"""
    timestamp = getattr(environment, "run_id", datetime.now().strftime("%Y%m%d_%H%M%S"))

    # 1. 写自定义汇总 JSON
    stats = environment.stats
    summary = {
        "timestamp": timestamp,
        "host": environment.host,
        "total_requests": stats.total.num_requests,
        "total_failures": stats.total.num_failures,
        "failure_rate": (
            stats.total.num_failures / stats.total.num_requests
            if stats.total.num_requests > 0
            else 0
        ),
        "avg_response_time_ms": stats.total.avg_response_time,
        "p50_response_time_ms": stats.total.get_response_time_percentile(0.5),
        "p95_response_time_ms": stats.total.get_response_time_percentile(0.95),
        "p99_response_time_ms": stats.total.get_response_time_percentile(0.99),
        "max_response_time_ms": stats.total.max_response_time,
        "rps": stats.total.total_rps,
        "endpoints": {},
    }

    for name, s in stats.entries.items():
        summary["endpoints"][name] = {
            "method": s.method,
            "num_requests": s.num_requests,
            "num_failures": s.num_failures,
            "avg_response_time_ms": s.avg_response_time,
            "p95_response_time_ms": s.get_response_time_percentile(0.95),
            "p99_response_time_ms": s.get_response_time_percentile(0.99),
            "rps": s.total_rps,
        }

    json_path = REPORT_DIR / f"loadtest_{timestamp}_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info(f"📊 Summary JSON: {json_path}")

    # 2. 控制台输出关键指标
    logger.info("=" * 60)
    logger.info("📈 Load Test Summary")
    logger.info("=" * 60)
    logger.info(f"Total Requests: {summary['total_requests']}")
    logger.info(f"Failures:        {summary['total_failures']} ({summary['failure_rate']*100:.2f}%)")
    logger.info(f"Avg RT:         {summary['avg_response_time_ms']:.0f} ms")
    logger.info(f"P95 RT:         {summary['p95_response_time_ms']:.0f} ms")
    logger.info(f"P99 RT:         {summary['p99_response_time_ms']:.0f} ms")
    logger.info(f"RPS:            {summary['rps']:.1f}")
    logger.info("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """记录慢请求(超过 3s)"""
    if response_time > 3000 and exception is None:
        logger.warning(f"⚠️  Slow request: {name} took {response_time:.0f}ms")
