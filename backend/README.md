"""后端 README"""
# 小Z简历 — 后端 (V1 商业化 MVP)

## 快速启动

### 1. 准备环境

```bash
# Python 3.11+
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env,至少填:
# - DATABASE_URL (PostgreSQL)
# - REDIS_URL
# - DEEPSEEK_API_KEY
# 开发模式 SMS_DEV_MODE=true,验证码固定 123456
```

### 3. 初始化数据库

```bash
# 方式 A:用 psql 直接跑 SQL
psql -U xiaoz -d xiaoz_resume -f ../db/01_schema.sql
psql -U xiaoz -d xiaoz_resume -f ../db/02_seed.sql

# 方式 B:用脚本
python -m scripts.init_db
```

### 4. 创建管理员

```bash
python -m scripts.create_admin 13800000000
```

### 5. 启动

```bash
python -m app.main
# 或
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问:
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 运行测试

```bash
pytest tests/ -v
```

## Docker 启动

```bash
# 整个项目
cd ..
docker compose up -d
```

只跑后端:
```bash
cd ..
docker compose up -d db redis backend
```

## 目录结构

```
backend/
├── app/
│   ├── main.py                # FastAPI 入口
│   ├── core/                  # 配置、DB、安全、缓存、短信、LLM、支付、OSS、限频
│   ├── models/                # 9 张表 SQLAlchemy 模型
│   ├── schemas/               # Pydantic 入参出参
│   ├── services/              # 业务逻辑
│   ├── api/v1/                # 22 个 API
│   │   ├── auth.py            # 鉴权
│   │   ├── user.py            # 用户
│   │   ├── files.py           # 文件
│   │   ├── rewrite.py         # 改写
│   │   ├── products.py        # 商品
│   │   ├── orders.py          # 订单 + 回调
│   │   ├── redeem.py          # 兑换码
│   │   ├── withdraw.py        # 提现(V1 仅查询)
│   │   └── admin/             # 后台 4 个模块
│   └── utils/                 # 工具(docx 解析等)
├── scripts/                   # 脚本(创建管理员、初始化 DB)
├── tests/                     # 单元测试
├── requirements.txt
└── .env.example
```

## 22 个 API 清单

### 用户端 (13 个)
- `POST /api/auth/send-sms` 发送验证码
- `POST /api/auth/login` 登录/注册
- `GET /api/user/me` 我的信息
- `POST /api/files/upload` 上传简历
- `GET /api/files` 文件列表
- `DELETE /api/files/:id` 删除文件
- `POST /api/rewrite/partial` 部分改写(50 积分)
- `POST /api/rewrite/full` 完整改写(1000/1500 积分)
- `GET /api/products` 商品列表
- `POST /api/orders` 创建订单
- `GET /api/orders/:no/pay-url` 支付链接
- `POST /api/redeem` 激活兑换码
- `GET /api/withdraw/balance` 提现余额查询
- `POST /api/orders/hupijiao/notify` 虎皮椒回调(无鉴权)

### 后台 (9 个)
- `GET /api/admin/dashboard/overview` 4 个核心指标
- `GET /api/admin/orders` 订单列表
- `GET /api/admin/orders/:no` 订单详情
- `POST /api/admin/orders/:no/refund` 退款
- `POST /api/admin/codes/generate` 批量生成兑换码
- `GET /api/admin/codes` 兑换码列表
- `POST /api/admin/codes/:id/revoke` 作废
- `GET /api/admin/codes/export` 导出 CSV
- `GET /api/admin/users` 用户列表
- `GET /api/admin/users/:id` 用户详情
- `POST /api/admin/users/:id/disable` 禁用
- `POST /api/admin/users/:id/enable` 启用
- `POST /api/admin/users/:id/adjust-points` 调整积分
