# ============================================================
# 小Z简历 - 本地开发 Makefile
# ============================================================
# 用法:
#   make help           - 看所有命令
#   make install        - 装所有依赖(后端+两个前端)
#   make init-db        - 初始化数据库(执行 schema.sql + seed.sql)
#   make test           - 跑后端单元测试
#   make smoke          - 端到端冒烟测试(需先 make run-be)
#   make run-be         - 起后端(localhost:8000)
#   make run-fe-user    - 起用户端(localhost:5173)
#   make run-fe-admin   - 起后台(localhost:5174)
#   make docker-up      - docker compose 一键起 5 服务
#   make docker-down    - 关停
#   make clean          - 清缓存/临时文件
#   make seed-dev       - 灌测试数据
#   make db-migrate     - Alembic 升级到最新
#   make db-revision    - 生成新迁移(自动)
# ============================================================

# ---------- 路径 ----------
BACKEND_DIR  := backend
FRONTEND_USER_DIR := frontend-user
FRONTEND_ADMIN_DIR := frontend-admin
DB_DIR       := db

# ---------- Python 虚拟环境(可覆盖) ----------
PYTHON       ?= python3
PIP          ?= $(PYTHON) -m pip
VENV_DIR     ?= $(BACKEND_DIR)/.venv
VENV_PYTHON  := $(VENV_DIR)/bin/python
VENV_PIP     := $(VENV_DIR)/bin/pip

# ---------- DB 配置(从 .env 读,这里给默认值) ----------
DB_HOST      ?= localhost
DB_PORT      ?= 5432
DB_USER      ?= xiaoz
DB_PASSWORD  ?= xiaoz_pwd
DB_NAME      ?= xiaoz_resume

# ---------- 帮助 ----------
.PHONY: help
help:
	@echo ""
	@echo "小Z简历 - 本地开发命令"
	@echo ""
	@echo "  初始化:"
	@echo "    make install         装后端+两个前端依赖"
	@echo "    make init-db         初始化数据库(schema+seed)"
	@echo "    make seed-dev        灌测试数据(3 用户+兑换码+订单)"
	@echo ""
	@echo "  启动服务(独立终端分别跑):"
	@echo "    make run-be          后端 http://localhost:8000"
	@echo "    make run-fe-user     用户端 http://localhost:5173"
	@echo "    make run-fe-admin    后台 http://localhost:5174"
	@echo ""
	@echo "  测试:"
	@echo "    make test            单元测试(pytest)"
	@echo "    make smoke           端到端冒烟(需先 make run-be)"
	@echo "    make lint            ruff + black 检查"
	@echo "    make format          自动 black 格式化"
	@echo ""
	@echo "  数据库迁移:"
	@echo "    make db-migrate      升级到最新"
	@echo "    make db-revision MSG='add xxx'  生成新迁移"
	@echo "    make db-downgrade    回退一个版本"
	@echo "    make db-history      看迁移历史"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-up       一键起 5 服务"
	@echo "    make docker-down     关停"
	@echo "    make docker-logs     看日志"
	@echo "    make docker-rebuild  重新构建并起"
	@echo ""
	@echo "  清理:"
	@echo "    make clean           清 .pyc / node_modules(可选)"
	@echo ""

# ---------- 装依赖 ----------
.PHONY: install
install: install-backend install-fe
	@echo "✓ 全部依赖装好"

.PHONY: install-backend
install-backend:
	@echo "➜ 装后端依赖..."
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	@echo "✓ 后端依赖 OK"

.PHONY: install-fe
install-fe: install-fe-user install-fe-admin
	@echo "✓ 前端依赖 OK"

.PHONY: install-fe-user
install-fe-user:
	@echo "➜ 装用户端依赖..."
	cd $(FRONTEND_USER_DIR) && npm install
	@echo "✓ 用户端依赖 OK"

.PHONY: install-fe-admin
install-fe-admin:
	@echo "➜ 装后台依赖..."
	cd $(FRONTEND_ADMIN_DIR) && npm install
	@echo "✓ 后台依赖 OK"

# ---------- 数据库 ----------
.PHONY: init-db
init-db:
	@echo "➜ 初始化数据库 $(DB_NAME)@$(DB_HOST)..."
	cd $(BACKEND_DIR) && DB_HOST=$(DB_HOST) DB_PORT=$(DB_PORT) DB_USER=$(DB_USER) \
		DB_PASSWORD=$(DB_PASSWORD) DB_NAME=$(DB_NAME) \
		$(PYTHON) scripts/init_db.py
	@echo "✓ 数据库初始化完成"

.PHONY: seed-dev
seed-dev:
	@echo "➜ 灌测试数据..."
	cd $(BACKEND_DIR) && DB_HOST=$(DB_HOST) DB_PORT=$(DB_PORT) DB_USER=$(DB_USER) \
		DB_PASSWORD=$(DB_PASSWORD) DB_NAME=$(DB_NAME) \
		$(PYTHON) scripts/seed_dev_data.py
	@echo "✓ 测试数据灌好"

# ---------- Alembic ----------
.PHONY: db-migrate
db-migrate:
	@echo "➜ Alembic upgrade head..."
	cd $(BACKEND_DIR) && alembic upgrade head
	@echo "✓ 迁移完成"

.PHONY: db-revision
db-revision:
	@if [ -z "$(MSG)" ]; then echo "用法: make db-revision MSG='add xxx'"; exit 1; fi
	cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$(MSG)"

.PHONY: db-downgrade
db-downgrade:
	cd $(BACKEND_DIR) && alembic downgrade -1

.PHONY: db-history
db-history:
	cd $(BACKEND_DIR) && alembic history --verbose

# ---------- 启动服务 ----------
.PHONY: run-be
run-be:
	@echo "➜ 启动后端 http://localhost:8000"
	@echo "   Swagger UI: http://localhost:8000/docs"
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run-fe-user
run-fe-user:
	@echo "➜ 启动用户端 http://localhost:5173"
	cd $(FRONTEND_USER_DIR) && npm run dev

.PHONY: run-fe-admin
run-fe-admin:
	@echo "➜ 启动后台 http://localhost:5174"
	cd $(FRONTEND_ADMIN_DIR) && npm run dev

# ---------- 测试 ----------
.PHONY: test
test:
	@echo "➜ 跑单元测试..."
	cd $(BACKEND_DIR) && pytest tests/ -v --tb=short
	@echo "✓ 测试完成"

.PHONY: smoke
smoke:
	@echo "➜ 跑端到端冒烟测试..."
	@echo "   (确保 make run-be 已在另一终端启动)"
	cd $(BACKEND_DIR) && bash tests/smoke_test.sh

.PHONY: lint
lint:
	@echo "➜ ruff 检查..."
	cd $(BACKEND_DIR) && ruff check app/ tests/ scripts/ || true
	@echo "➜ black 格式检查..."
	cd $(BACKEND_DIR) && black --check --diff app/ tests/ scripts/ || true

.PHONY: format
format:
	@echo "➜ black 格式化..."
	cd $(BACKEND_DIR) && black app/ tests/ scripts/
	@echo "✓ 格式化完成"

# ---------- Docker ----------
.PHONY: docker-up
docker-up:
	@echo "➜ docker compose up -d..."
	docker compose up -d
	@echo "✓ 5 服务已起"
	@echo "  用户端: http://localhost"
	@echo "  后台:   http://localhost/admin"
	@echo "  API:    http://localhost/api/docs"

.PHONY: docker-down
docker-down:
	docker compose down

.PHONY: docker-logs
docker-logs:
	docker compose logs -f --tail=100

.PHONY: docker-rebuild
docker-rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

# ---------- 清理 ----------
.PHONY: clean
clean:
	@echo "➜ 清理 Python 缓存..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Python 缓存清理完成"
	@echo "(如需清 node_modules,执行: rm -rf $(FRONTEND_USER_DIR)/node_modules $(FRONTEND_ADMIN_DIR)/node_modules)"

# ---------- 快捷:一键起本地全栈 ----------
.PHONY: dev
dev:
	@echo "一键起本地全栈(需 4 个终端分别跑下列命令):"
	@echo "  1. make init-db     # 首次需要"
	@echo "  2. make run-be      # 终端 A"
	@echo "  3. make run-fe-user # 终端 B"
	@echo "  4. make run-fe-admin# 终端 C"
