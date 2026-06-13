"""V2 - 管理员操作日志表

Revision ID: 0002_operation_logs
Revises: 0001_initial
Create Date: 2026-06-06 01:35:00

新增 1 张表:
  - operation_logs: 管理员操作审计(append-only)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_operation_logs"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operation_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("admin_id", sa.BigInteger, nullable=False),
        sa.Column("admin_phone", sa.String(20), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50)),
        sa.Column("target_id", sa.BigInteger),
        sa.Column("before_value", postgresql.JSONB),
        sa.Column("after_value", postgresql.JSONB),
        sa.Column("remark", sa.Text),
        sa.Column("ip", sa.String(64)),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_operation_logs_admin", "operation_logs", ["admin_id"])
    op.create_index("idx_operation_logs_action", "operation_logs", ["action"])
    op.create_index("idx_operation_logs_created", "operation_logs", [sa.text("created_at DESC")])
    op.execute("COMMENT ON TABLE operation_logs IS '管理员操作审计日志,append-only'")


def downgrade() -> None:
    op.drop_table("operation_logs")
