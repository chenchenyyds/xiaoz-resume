"""V1 商业化 MVP - 初始 9 张表

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-06 01:05:00

对应 SQL: db/01_schema.sql
后续 V2 改动(如加表/加列)请新建 0002_xxx.py 迁移文件,不要修改本文件。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- 扩展 ----------
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ---------- 1. users ----------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("phone", sa.String(20), unique=True, nullable=False),
        sa.Column("nickname", sa.String(50)),
        sa.Column("avatar_url", sa.String(512)),
        sa.Column("invite_code", sa.String(16), unique=True),
        sa.Column("invite_user_id", sa.BigInteger),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("is_admin", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("last_active_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_users_invite_user_id", "users", ["invite_user_id"])
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index("idx_users_created_at", "users", [sa.text("created_at DESC")])
    op.execute("COMMENT ON TABLE users IS '用户表,V1 仅手机号+验证码,无密码'")

    # ---------- 2. sms_codes ----------
    op.create_table(
        "sms_codes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("code", sa.String(6), nullable=False),
        sa.Column("used", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("expire_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_sms_codes_phone_used", "sms_codes", ["phone", "used", sa.text("expire_at DESC")])
    op.execute("COMMENT ON TABLE sms_codes IS '短信验证码,1 分钟内同号不发'")

    # ---------- 3. point_accounts ----------
    op.create_table(
        "point_accounts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("point_type", sa.String(20), nullable=False),
        sa.Column("balance", sa.Integer, server_default="0", nullable=False),
        sa.Column("total_earned", sa.Integer, server_default="0", nullable=False),
        sa.Column("total_used", sa.Integer, server_default="0", nullable=False),
        sa.Column("expire_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("source", sa.String(50)),
        sa.Column("related_id", sa.BigInteger),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_point_accounts_user_type", "point_accounts", ["user_id", "point_type"])
    op.execute(
        "CREATE INDEX idx_point_accounts_user_balance ON point_accounts(user_id, balance) WHERE balance > 0"
    )
    op.execute("COMMENT ON TABLE point_accounts IS '积分账户批次表,按 FIFO 消耗'")

    # ---------- 4. point_transactions ----------
    op.create_table(
        "point_transactions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("point_type", sa.String(20), nullable=False),
        sa.Column("change", sa.Integer, nullable=False),
        sa.Column("balance_before", sa.Integer),
        sa.Column("balance_after", sa.Integer),
        sa.Column("source", sa.String(50)),
        sa.Column("related_id", sa.BigInteger),
        sa.Column("feature", sa.String(50)),
        sa.Column("remark", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_point_transactions_user_created", "point_transactions", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_point_transactions_user_feature", "point_transactions", ["user_id", "feature", sa.text("created_at DESC")])
    op.execute("COMMENT ON TABLE point_transactions IS '积分流水,append-only'")

    # ---------- 5. orders ----------
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("order_no", sa.String(32), unique=True, nullable=False),
        sa.Column("user_id", sa.BigInteger),
        sa.Column("product_code", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("pay_amount", sa.Numeric(10, 2)),
        sa.Column("pay_channel", sa.String(20)),
        sa.Column("pay_trade_no", sa.String(64)),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("invite_user_id", sa.BigInteger),
        sa.Column("redeem_code_id", sa.BigInteger),
        sa.Column("paid_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("refunded_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("refund_amount", sa.Numeric(10, 2)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_orders_user", "orders", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_invite_user", "orders", ["invite_user_id", sa.text("created_at DESC")])
    op.execute("COMMENT ON TABLE orders IS '订单表,状态机 pending→paid→refunded/closed'")

    # ---------- 6. redeem_codes ----------
    op.create_table(
        "redeem_codes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("code_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("code_mask", sa.String(20), nullable=False),
        sa.Column("points", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), server_default="unused", nullable=False),
        sa.Column("used_by", sa.BigInteger),
        sa.Column("used_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("note", sa.String(100)),
        sa.Column("created_by", sa.BigInteger),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("expire_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_redeem_codes_status", "redeem_codes", ["status"])
    op.execute("COMMENT ON TABLE redeem_codes IS '兑换码,明文只生成时返回一次,DB 只存 hash'")

    # ---------- 7. resume_files ----------
    op.create_table(
        "resume_files",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_format", sa.String(20), nullable=False),
        sa.Column("file_url", sa.String(512)),
        sa.Column("file_size", sa.Integer),
        sa.Column("content_text", sa.Text),
        sa.Column("content_json", postgresql.JSONB),
        sa.Column("title", sa.String(255)),
        sa.Column("with_jd", sa.Boolean, server_default=sa.text("false")),
        sa.Column("jd_text", sa.Text),
        sa.Column("is_deleted", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_resume_files_user", "resume_files", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_resume_files_user_active", "resume_files", ["user_id", "is_deleted"])
    op.execute("COMMENT ON TABLE resume_files IS '简历文件,V1 只支持 docx'")

    # ---------- 8. rewrite_records ----------
    op.create_table(
        "rewrite_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("feature", sa.String(50), nullable=False),
        sa.Column("source_file_id", sa.BigInteger),
        sa.Column("input_text", sa.Text),
        sa.Column("jd_text", sa.Text),
        sa.Column("title", sa.String(50)),
        sa.Column("style_hint", sa.String(100)),
        sa.Column("generated_file_id", sa.BigInteger),
        sa.Column("output_text", sa.Text),
        sa.Column("improvement_points", postgresql.JSONB),
        sa.Column("points_cost", sa.Integer, nullable=False),
        sa.Column("point_transaction_id", sa.BigInteger),
        sa.Column("model_name", sa.String(50)),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_rewrite_records_user_created", "rewrite_records", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_rewrite_records_user_feature", "rewrite_records", ["user_id", "feature", sa.text("created_at DESC")])
    op.execute("COMMENT ON TABLE rewrite_records IS '改写记录,含 LLM 调用量'")

    # ---------- 9. system_configs ----------
    op.create_table(
        "system_configs",
        sa.Column("config_key", sa.String(100), primary_key=True),
        sa.Column("config_value", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.execute("COMMENT ON TABLE system_configs IS '系统配置,所有可变业务参数都从这里读'")

    # ---------- 触发器 ----------
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for tbl in ("point_accounts", "orders", "system_configs"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl}")
        op.execute(f"""
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)


def downgrade() -> None:
    """回退:按依赖反序删除"""
    for tbl in (
        "rewrite_records", "resume_files", "redeem_codes", "orders",
        "point_transactions", "point_accounts", "sms_codes", "users", "system_configs",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl}")
        op.drop_table(tbl)

    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
