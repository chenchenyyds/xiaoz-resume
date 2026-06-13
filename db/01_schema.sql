-- =====================================================
-- 小Z简历 — V1 商业化 MVP 数据库 Schema
-- 9 张表 + 必要索引
-- 适配 PostgreSQL 15+
-- =====================================================

-- 扩展（如果用 citext、uuid 等）
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------- 1. 用户 ----------
CREATE TABLE IF NOT EXISTS users (
  id              BIGSERIAL PRIMARY KEY,
  phone           VARCHAR(20) UNIQUE NOT NULL,
  nickname        VARCHAR(50),
  avatar_url      VARCHAR(512),
  invite_code     VARCHAR(16) UNIQUE,         -- 用户的推广码
  invite_user_id  BIGINT,                     -- 上级推广人
  status          VARCHAR(20) DEFAULT 'active' NOT NULL,  -- active/disabled
  is_admin        BOOLEAN DEFAULT FALSE NOT NULL,        -- 简易后台标记
  created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  last_active_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_users_invite_user_id ON users(invite_user_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

COMMENT ON TABLE users IS '用户表，V1 仅手机号+验证码，无密码';

-- ---------- 2. 短信验证码 ----------
CREATE TABLE IF NOT EXISTS sms_codes (
  id          BIGSERIAL PRIMARY KEY,
  phone       VARCHAR(20) NOT NULL,
  code        VARCHAR(6)  NOT NULL,
  used        BOOLEAN DEFAULT FALSE NOT NULL,
  expire_at   TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sms_codes_phone_used ON sms_codes(phone, used, expire_at DESC);
COMMENT ON TABLE sms_codes IS '短信验证码，1 分钟内同号不发';

-- ---------- 3. 积分账户 ----------
-- 一条记录 = 一种类型的一个批次
CREATE TABLE IF NOT EXISTS point_accounts (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT NOT NULL,
  point_type    VARCHAR(20) NOT NULL,        -- trial/subscription/purchase
  balance       INT DEFAULT 0 NOT NULL,
  total_earned  INT DEFAULT 0 NOT NULL,
  total_used    INT DEFAULT 0 NOT NULL,
  expire_at     TIMESTAMPTZ,                 -- NULL=永久
  source        VARCHAR(50),                 -- trial/invite/order/...
  related_id    BIGINT,                      -- 关联订单/兑换码等
  created_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_point_accounts_user_type
  ON point_accounts(user_id, point_type);
CREATE INDEX IF NOT EXISTS idx_point_accounts_user_balance
  ON point_accounts(user_id, balance) WHERE balance > 0;
COMMENT ON TABLE point_accounts IS '积分账户批次表，按 FIFO 消耗';

-- ---------- 4. 积分流水 ----------
CREATE TABLE IF NOT EXISTS point_transactions (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT NOT NULL,
  point_type      VARCHAR(20) NOT NULL,
  change          INT NOT NULL,                -- 正=获得，负=消耗
  balance_before  INT,
  balance_after   INT,
  source          VARCHAR(50),                 -- trial/rewrite/order/redeem/...
  related_id      BIGINT,
  feature         VARCHAR(50),                 -- partial_rewrite/full_rewrite/...
  remark          TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_point_transactions_user_created
  ON point_transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_point_transactions_user_feature
  ON point_transactions(user_id, feature, created_at DESC);
COMMENT ON TABLE point_transactions IS '积分流水，append-only';

-- ---------- 5. 订单 ----------
CREATE TABLE IF NOT EXISTS orders (
  id              BIGSERIAL PRIMARY KEY,
  order_no        VARCHAR(32) UNIQUE NOT NULL,
  user_id         BIGINT,
  product_code    VARCHAR(50) NOT NULL,        -- single/monthly/points_1000
  amount          DECIMAL(10,2) NOT NULL,
  pay_amount      DECIMAL(10,2),
  pay_channel     VARCHAR(20),                 -- hupijiao/wxpay/alipay
  pay_trade_no    VARCHAR(64),
  status          VARCHAR(20) DEFAULT 'pending' NOT NULL,  -- pending/paid/refunded/closed
  invite_user_id  BIGINT,                      -- 成交时的推广人
  redeem_code_id  BIGINT,                      -- 兑换码下单时关联
  paid_at         TIMESTAMPTZ,
  refunded_at     TIMESTAMPTZ,
  refund_amount   DECIMAL(10,2),
  created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_product ON orders(product_code, created_at DESC);
COMMENT ON TABLE orders IS '订单表，V1 仅虎皮椒支付';

-- ---------- 6. 兑换码 ----------
CREATE TABLE IF NOT EXISTS redeem_codes (
  id              BIGSERIAL PRIMARY KEY,
  code_hash       VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 后的码
  code_mask       VARCHAR(32) NOT NULL,         -- 用于展示/导出的脱敏码
  type            VARCHAR(20) NOT NULL,         -- single/monthly/points_1000/trial
  points          INT NOT NULL,
  status          VARCHAR(20) DEFAULT 'unused' NOT NULL,  -- unused/used/revoked
  batch_id        VARCHAR(32),                 -- 批次号
  order_id        BIGINT,                       -- 通过订单生成时回填
  user_id         BIGINT,                       -- 被谁激活
  used_at         TIMESTAMPTZ,
  expire_at       TIMESTAMPTZ,                  -- 兑换码本身的过期
  invite_user_id  BIGINT,                       -- 售出时的推广人
  created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_redeem_codes_batch ON redeem_codes(batch_id);
CREATE INDEX IF NOT EXISTS idx_redeem_codes_status ON redeem_codes(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_redeem_codes_user ON redeem_codes(user_id);
COMMENT ON TABLE redeem_codes IS '兑换码，码值存 hash 防泄漏';

-- ---------- 7. 简历文件 ----------
CREATE TABLE IF NOT EXISTS resume_files (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT NOT NULL,
  type          VARCHAR(20) NOT NULL,          -- uploaded/generated
  file_name     VARCHAR(255) NOT NULL,
  file_format   VARCHAR(20) NOT NULL,          -- docx
  file_url      VARCHAR(512),                  -- OSS 地址
  file_size     INT,
  content_text  TEXT,                          -- 解析后纯文本
  content_json  JSONB,                         -- 解析后结构化
  title         VARCHAR(255),
  with_jd       BOOLEAN DEFAULT FALSE,
  jd_text       TEXT,
  is_deleted    BOOLEAN DEFAULT FALSE NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_resume_files_user ON resume_files(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_resume_files_user_active ON resume_files(user_id, is_deleted);
COMMENT ON TABLE resume_files IS '简历文件，V1 只支持 docx';

-- ---------- 8. 改写记录 ----------
CREATE TABLE IF NOT EXISTS rewrite_records (
  id                      BIGSERIAL PRIMARY KEY,
  user_id                 BIGINT NOT NULL,
  feature                 VARCHAR(50) NOT NULL,  -- partial_rewrite/full_rewrite/full_rewrite_with_jd
  source_file_id          BIGINT,
  input_text              TEXT,                  -- 部分改写时为原文
  jd_text                 TEXT,
  title                   VARCHAR(50),
  style_hint              VARCHAR(100),
  generated_file_id       BIGINT,                -- 完整改写时回写
  output_text             TEXT,                  -- 改写后内容
  improvement_points      JSONB,                 -- 5 条优化点
  points_cost             INT NOT NULL,
  point_transaction_id    BIGINT,
  model_name              VARCHAR(50),
  input_tokens            INT,
  output_tokens           INT,
  duration_ms             INT,
  created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rewrite_records_user_created
  ON rewrite_records(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rewrite_records_user_feature
  ON rewrite_records(user_id, feature, created_at DESC);
COMMENT ON TABLE rewrite_records IS '改写记录，含 LLM 调用量';

-- ---------- 9. 系统配置（key-value）----------
CREATE TABLE IF NOT EXISTS system_configs (
  config_key    VARCHAR(100) PRIMARY KEY,
  config_value  TEXT NOT NULL,
  description   TEXT,
  updated_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
COMMENT ON TABLE system_configs IS '系统配置，所有可变业务参数都从这里读';

-- =====================================================
-- 触发器：updated_at 自动更新
-- =====================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_point_accounts_updated_at ON point_accounts;
CREATE TRIGGER trg_point_accounts_updated_at
  BEFORE UPDATE ON point_accounts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_orders_updated_at ON orders;
CREATE TRIGGER trg_orders_updated_at
  BEFORE UPDATE ON orders
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_system_configs_updated_at ON system_configs;
CREATE TRIGGER trg_system_configs_updated_at
  BEFORE UPDATE ON system_configs
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
