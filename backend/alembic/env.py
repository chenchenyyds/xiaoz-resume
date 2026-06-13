"""Alembic 环境配置
- 从 app.core.config 读 DATABASE_URL
- 启用 SQLAlchemy 模型自动比对(--autogenerate 才有效)
- 支持离线生成 SQL
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------- 让 alembic 能 import app ----------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.core.database import Base    # noqa: E402

# 导入所有模型(让 autogenerate 能发现)
from app.models import (  # noqa: E402,F401
    user, sms_code, point, order, redeem, resume, rewrite, config,
)

config = context.config

# ---------- 用环境变量覆盖 sqlalchemy.url ----------
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ---------- 日志 ----------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------- metadata target ----------
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式:只生成 SQL 不执行(给生产运维用)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,        # 检测列类型变化
        compare_server_default=True,  # 检测默认值变化
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式:连库直接执行"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # 事务包裹(默认)
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
