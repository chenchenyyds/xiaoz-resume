# 小Z简历 - Locust 压测指南

> 模拟 4 类用户行为,覆盖 6 个核心 API,验证系统在不同并发下的性能表现。

## 快速开始

### 1. 安装依赖

```bash
cd scripts/loadtest
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 启动被测服务

```bash
# 方式 1:本地 dev
cd /app/data/所有对话/主对话/小Z简历/代码
make run-be

# 方式 2:Docker 全栈
cd /app/data/所有对话/主对话/小Z简历/代码
docker compose up -d backend
```

### 3. 启动压测(Web UI)

```bash
cd scripts/loadtest
locust -f locustfile.py --host=http://localhost:8000
```

打开 http://localhost:8089,在 Web UI 配置:
- Users: 100
- Spawn rate: 10
- Host: http://localhost:8000

### 4. 启动压测(命令行,无 UI)

```bash
# 100 用户,持续 5 分钟
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html reports/loadtest_100u_5m.html
```

### 5. 阶梯加压(推荐)

```bash
# 10/50/100/200 阶梯
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --html reports/loadtest_step.html \
  StepLoadShape
```

## 用户类型

| 类型 | Weight | 行为 |
|------|--------|------|
| AnonymousUser | 3 | 浏览商品、发送验证码、注册 |
| TrialUser | 4 | 注册登录,中频改写(50 积分),偶尔上传 |
| PaidUser | 2 | 登录,高频部分改写,含 JD 完整改写,下单 |
| VIPUser | 1 | 极限压测,1 秒 1 次改写 |

## 覆盖 API

| 端点 | 任务权重 | 用户 |
|------|---------|------|
| `POST /auth/send-sms` | 2 | anonymous |
| `POST /auth/login` | 1 | anonymous/trial/paid/vip |
| `GET /user/me` | 5 | trial |
| `POST /files/upload` | 2 | trial/paid |
| `POST /rewrite/partial` | 5-20 | trial/paid/vip |
| `POST /rewrite/full` | 1-5 | trial/paid/vip |
| `POST /orders` | 2 | paid |
| `GET /products` | 8 | anonymous |

## 报告输出

压测结束后,会在 `reports/` 目录生成:

```
reports/
├── loadtest_<timestamp>_summary.json    # 关键指标 JSON 汇总
├── loadtest_<timestamp>.html            # Locust 原始 HTML 报告
├── loadtest_<timestamp>_stats.csv       # 每个端点统计
└── loadtest_<timestamp>_failures.csv    # 失败请求详情
```

## 关键指标

压测结束后查看 `_summary.json` 中的:

| 指标 | 健康阈值 |
|------|---------|
| **failure_rate** | < 0.1% |
| **p95_response_time_ms** | < 1000 ms |
| **p99_response_time_ms** | < 3000 ms |
| **RPS** | > 50(单实例) |

## 故障排查

### 1. 大量 401 错误

- 检查 JWT_SECRET_KEY 是否一致
- 检查 dev 环境是否开放测试账号

### 2. 大量 429 错误(限流)

- 这是**正常行为**,限流系统在工作
- 降低 `--users` 或 `--spawn-rate`

### 3. 大量 500 错误

- 检查后端日志:`docker compose logs backend`
- 检查 DeepSeek API key 是否有效
- 检查数据库连接数

### 4. Locust 卡死

- 降低并发数
- 检查 `gevent` 是否正确安装

## 进阶:分布式压测

```bash
# Master 节点
locust -f locustfile.py --master --host=http://localhost:8000

# Worker 节点(多机)
locust -f locustfile.py --worker --master-host=<master_ip>
```

## 集成到 CI

```yaml
# .github/workflows/loadtest.yml
- name: Locust smoke test
  run: |
    cd scripts/loadtest
    pip install -r requirements.txt
    locust -f locustfile.py \
      --host=http://staging.xiaoz-jl.com \
      --users 10 --spawn-rate 2 --run-time 30s \
      --headless --exit-code-on-error 1
```

## 安全声明

- 本压测脚本仅用于**自测试**,勿对未授权系统使用
- 测试数据使用模拟手机号池,不会影响真实用户
- 测试完成后清理 Locust 进程,避免资源泄漏
