# 小Z简历 - V1 商业化 MVP

> **面向**：个人开发者(主人)
> **目标**：用最小成本、最短时间,做出可商业化落地的 AI 简历优化 SaaS
> **技术栈**：FastAPI + PostgreSQL + Redis + DeepSeek + Vue 3 + Docker
> **当前阶段**：V1 MVP 已完成代码骨架,等待电脑回来联调上线

---

## 📂 目录结构(120 个文件)

```
代码/
├── README.md             ← 你正在看
├── Makefile              ← 本地开发命令(make help 看全部)
├── docker-compose.yml    ← 一键起 5 服务:db/redis/backend/2 frontend/nginx
├── .env.example          ← 环境变量模板(复制成 .env 后填值)
├── .gitignore            ← 避免敏感文件入库
│
├── db/                   ← 数据库
│   ├── 01_schema.sql     ← 9 张表 DDL(可读,参考用)
│   └── 02_seed.sql       ← 33 项 system_configs seed
│
├── backend/              ← FastAPI 后端(60+ 文件)
│   ├── alembic/          ← 数据库迁移(V2 必备)
│   │   ├── env.py
│   │   └── versions/0001_initial.py
│   ├── app/
│   │   ├── main.py       ← 入口
│   │   ├── core/         ← 11 个:config/database/security/cache/llm/payment/oss/sms/...
│   │   ├── models/       ← 9 张表 SQLAlchemy 模型
│   │   ├── schemas/      ← 8 个 Pydantic 入参出参
│   │   ├── services/     ← 7 个核心服务(★ points_service = FIFO 核心)
│   │   ├── api/v1/       ← 22 个 API 端点
│   │   └── utils/        ← docx_parser
│   ├── tests/            ← 测试
│   │   ├── test_points_fifo.py  ← 6 个 FIFO 用例
│   │   ├── test_redeem.py       ← 6 个兑换码用例
│   │   ├── test_orders.py       ← 5 个订单用例
│   │   └── smoke_test.sh        ← 端到端冒烟(16 步)
│   ├── scripts/
│   │   ├── init_db.py           ← 跑 SQL 文件初始化
│   │   ├── create_admin.py      ← 改管理员
│   │   └── seed_dev_data.py     ← 灌测试数据(3 用户+兑换码+订单)
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   └── README.md
│
├── frontend-user/        ← 用户端(Vue 3 + Vant)
│   ├── src/
│   │   ├── main.ts       ← 5 路由入口
│   │   ├── views/        ← Login / Workbench / Files / Redeem / Me
│   │   ├── components/   ← PartialRewrite / FullRewrite / ShopPanel
│   │   ├── api/          ← http / auth / user / files / rewrite / shop
│   │   ├── stores/       ← Pinia user store
│   │   └── styles/
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
│
├── frontend-admin/       ← 后台(Vue 3 + Element Plus)
│   ├── src/
│   │   ├── main.ts       ← 嵌套 Layout 路由
│   │   ├── views/        ← Login / Layout / Dashboard / Orders / Codes / Users
│   │   ├── api/          ← http / dashboard / orders / codes / users
│   │   └── router/
│   ├── package.json
│   └── README.md
│
├── nginx/                ← 反向代理
│   └── nginx.conf        ← /api/ 反代到 backend,/admin/ 反代到 admin 前端
│
├── docs/                 ← 详细文档
│   ├── API.md            ← 22 个 API 详解
│   ├── DEPLOY.md         ← 5 种部署方式(本地/Docker/腾讯云/七牛/双 11)
│   ├── LOCAL_DEV.md      ← 本地开发技巧
│   ├── BUSINESS_RULES.md ← 业务规则详解
│   └── PROMPT_DESIGN.md  ← 3 个 prompt 设计说明
│
└── .github/workflows/    ← CI
    ├── backend-test.yml  ← pytest + PG + Redis 服务
    ├── backend-lint.yml  ← ruff + black
    └── frontend-build.yml← npm ci + build
```

---

## 🚀 5 分钟启动(本地)

```bash
# 1) 复制环境变量模板
cd 代码/backend
cp .env.example .env
# 编辑 .env 填必填项:DEEPSEEK_API_KEY / JWT_SECRET_KEY

# 2) 回到根目录
cd ..

# 3) 一键起 PG + Redis
docker compose up -d db redis

# 4) 初始化数据库
make init-db

# 5) 灌测试数据(可选,带 3 个测试账号+兑换码)
make seed-dev

# 6) 启动后端
make run-be
# 看到 http://localhost:8000/docs 即可

# 7) (新终端)启动用户端
make run-fe-user
# http://localhost:5173

# 8) (新终端)启动后台
make run-fe-admin
# http://localhost:5174
```

**测试账号**(灌了 seed_dev 之后):
- 管理员:`13800000000` / 验证码 `123456`
- 用户 A:`13800000001` / `123456` (有积分有简历)
- 用户 B/C:被 A 推广

---

## 🧪 跑测试

```bash
# 单元测试(17 个)
make test

# 端到端冒烟(16 步,需先 make run-be)
make smoke
```

**测试覆盖**:
- 积分 FIFO 消耗(6 用例:顺序/余额不足/过期/退款/余额汇总/grant)
- 兑换码(6 用例:生成/兑换/重复/作废/脱敏)
- 订单(5 用例:创建/支付/退款/返佣/状态机)

---

## 🐳 一键 Docker 起全栈

```bash
cd 代码
docker compose up -d

# 访问:
#   用户端:http://localhost
#   后台:  http://localhost/admin
#   API:   http://localhost/api/docs
```

5 个服务:`db / redis / backend / frontend-user / frontend-admin / nginx`

---

## 📊 当前进度(任务 E 清单回顾)

✅ **AI 已完成(113+ 个文件)**:
- 数据库:9 张表 DDL + 33 项 seed
- 后端:60+ 文件,22 个 API,7 个核心服务
- 用户端:5 页面 + 3 组件
- 后台:5 页面
- Docker:Nginx + Compose
- 文档:5 份详细文档
- 测试:17 个单元测试 + smoke_test.sh 端到端
- **新增(本轮)**:Alembic 迁移 + GitHub Actions CI + Makefile + seed 脚本

⏳ **等电脑回来人工做**:
- 申请 DeepSeek / 虎皮椒 / 阿里云 OSS / 阿里云短信 等 5 个第三方账号
- 买腾讯云轻量 4C8G(¥200/月)
- 域名注册 + ICP 备案(7-20 天)
- 部署上线 → 内测 5 人 → 灰度推广

📅 **V1 6-8 周时间表**:累计 100 单 / 退款率 < 15% / 至少 1 个自发转发 即视为成功

---

## 🔧 常用命令速查

```bash
make help           # 看所有命令
make install        # 装全部依赖
make init-db        # 初始化数据库
make seed-dev       # 灌测试数据
make test           # 跑单元测试
make smoke          # 端到端冒烟
make run-be         # 后端
make run-fe-user    # 用户端
make run-fe-admin   # 后台
make docker-up      # Docker 全栈
make db-migrate     # Alembic 升级
make db-revision MSG='add xxx'  # 生成新迁移
make lint           # ruff + black
make format         # 自动格式化
make clean          # 清缓存
```

详细文档在 `docs/` 目录:
- `API.md` - 22 个 API 字段、错误码、示例
- `DEPLOY.md` - 部署到腾讯云步骤
- `BUSINESS_RULES.md` - 业务规则为什么这样设计
- `PROMPT_DESIGN.md` - 3 个改写 prompt 的设计思路
- `LOCAL_DEV.md` - 开发调试技巧
