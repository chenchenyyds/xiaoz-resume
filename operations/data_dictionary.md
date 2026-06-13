# 小Z简历 - 数据字典

> 9 张表的字段说明、索引、约束、数据生命周期。

---

## 1. users (用户表)

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| phone | VARCHAR(20) | ✅ | - | 手机号(唯一) |
| nickname | VARCHAR(50) | - | - | 昵称 |
| avatar_url | VARCHAR(512) | - | - | 头像 URL |
| invite_code | VARCHAR(16) | - | - | 推广码(唯一) |
| invite_user_id | BIGINT | - | - | 上级推广人 ID |
| status | VARCHAR(20) | ✅ | 'active' | active/disabled |
| is_admin | BOOLEAN | ✅ | false | 是否管理员 |
| created_at | TIMESTAMPTZ | ✅ | NOW() | 注册时间 |
| last_active_at | TIMESTAMPTZ | - | - | 最后活跃时间 |

**索引**:
- `idx_users_invite_user_id` ON (invite_user_id)
- `idx_users_status` ON (status)
- `idx_users_created_at` ON (created_at DESC)

**生命周期**:永久(注销后软删除,标记 status='disabled')

---

## 2. sms_codes (短信验证码)

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| phone | VARCHAR(20) | ✅ | - | 手机号 |
| code | VARCHAR(6) | ✅ | - | 6 位数字 |
| used | BOOLEAN | ✅ | false | 是否已使用 |
| expire_at | TIMESTAMPTZ | ✅ | - | 过期时间(发送时间 + 5 分钟) |
| created_at | TIMESTAMPTZ | ✅ | NOW() | 发送时间 |

**索引**:`idx_sms_codes_phone_used` ON (phone, used, expire_at DESC)

**生命周期**:验证后保留 30 天(用于审计),之后可清理

---

## 3. point_accounts (积分账户批次)

> **关键设计**: 一条记录 = 一种类型的一个批次。FIFO 消耗时按 (expire_at ASC, created_at ASC) 排序。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| user_id | BIGINT | ✅ | - | 用户 ID |
| point_type | VARCHAR(20) | ✅ | - | trial/subscription/purchase |
| balance | INT | ✅ | 0 | 当前余额(分) |
| total_earned | INT | ✅ | 0 | 累计获得 |
| total_used | INT | ✅ | 0 | 累计消耗 |
| expire_at | TIMESTAMPTZ | - | - | 到期时间(NULL=永久) |
| source | VARCHAR(50) | - | - | 来源:trial/order/redeem/invite/adjust |
| related_id | BIGINT | - | - | 关联 ID(订单/兑换码) |
| created_at | TIMESTAMPTZ | ✅ | NOW() | 批次创建时间 |
| updated_at | TIMESTAMPTZ | ✅ | NOW() | 最后更新时间 |

**索引**:
- `idx_point_accounts_user_type` ON (user_id, point_type)
- `idx_point_accounts_user_balance` ON (user_id, balance) WHERE balance > 0

**积分类型**:
- `trial`: 试用,90 天过期
- `subscription`: 订阅(月卡),30 天过期
- `purchase`: 增购,**永久有效**

**FIFO 消耗 SQL**:
```sql
SELECT * FROM point_accounts
WHERE user_id = ? AND balance > 0
  AND (expire_at IS NULL OR expire_at > NOW())
ORDER BY
  CASE point_type
    WHEN 'subscription' THEN 1
    WHEN 'trial' THEN 2
    WHEN 'purchase' THEN 3
  END,
  expire_at ASC NULLS LAST,
  created_at ASC
FOR UPDATE;
```

---

## 4. point_transactions (积分流水)

> **append-only**,任何积分变动都记录一条,不可修改不可删除。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| user_id | BIGINT | ✅ | - | 用户 ID |
| point_type | VARCHAR(20) | ✅ | - | 同账户 |
| change | INT | ✅ | - | 变动量(正=获得,负=消耗) |
| balance_before | INT | - | - | 变动前余额 |
| balance_after | INT | - | - | 变动后余额 |
| source | VARCHAR(50) | - | - | 来源 |
| related_id | BIGINT | - | - | 关联 |
| feature | VARCHAR(50) | - | - | 功能:partial_rewrite/full_rewrite |
| remark | TEXT | - | - | 备注 |
| created_at | TIMESTAMPTZ | ✅ | NOW() | - |

**索引**:
- `idx_point_transactions_user_created` ON (user_id, created_at DESC)
- `idx_point_transactions_user_feature` ON (user_id, feature, created_at DESC)

**生命周期**:永久(审计需要),可考虑 3 年后归档到冷库

---

## 5. orders (订单)

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| order_no | VARCHAR(32) | ✅ | - | 订单号(唯一,业务用) |
| user_id | BIGINT | - | - | 用户 ID |
| product_code | VARCHAR(50) | ✅ | - | single/monthly/points_1000 |
| amount | DECIMAL(10,2) | ✅ | - | 订单金额(元) |
| pay_amount | DECIMAL(10,2) | - | - | 实际支付金额 |
| pay_channel | VARCHAR(20) | - | - | hupijiao/wxpay/alipay |
| pay_trade_no | VARCHAR(64) | - | - | 支付渠道交易号 |
| status | VARCHAR(20) | ✅ | 'pending' | pending/paid/refunded/closed |
| invite_user_id | BIGINT | - | - | 成交时的推广人 |
| redeem_code_id | BIGINT | - | - | 兑换码下单时关联 |
| paid_at | TIMESTAMPTZ | - | - | 支付成功时间 |
| refunded_at | TIMESTAMPTZ | - | - | 退款时间 |
| refund_amount | DECIMAL(10,2) | - | - | 退款金额 |
| created_at | TIMESTAMPTZ | ✅ | NOW() | 下单时间 |
| updated_at | TIMESTAMPTZ | ✅ | NOW() | 更新时间 |

**索引**:
- `idx_orders_user` ON (user_id, created_at DESC)
- `idx_orders_status` ON (status)
- `idx_orders_invite_user` ON (invite_user_id, created_at DESC)

**状态机**:
```
pending ──┬─→ paid ──┬─→ refunded
          │           └─→ closed(超时未支付)
          └─→ closed(用户取消)
```

**生命周期**:**保留 3 年**(电商法规要求)

---

## 6. redeem_codes (兑换码)

> **安全**: 明文只生成时返回一次,DB 只存 SHA-256 hash,`code_mask` 脱敏展示。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| code_hash | VARCHAR(64) | ✅ | - | SHA-256 hash(唯一) |
| code_mask | VARCHAR(20) | ✅ | - | 脱敏:XXXX-****-XXXX |
| points | INT | ✅ | - | 兑换积分数 |
| status | VARCHAR(20) | ✅ | 'unused' | unused/used/revoked |
| used_by | BIGINT | - | - | 使用者用户 ID |
| used_at | TIMESTAMPTZ | - | - | 使用时间 |
| note | VARCHAR(100) | - | - | 备注(批次/活动) |
| created_by | BIGINT | - | - | 生成者(管理员 ID) |
| created_at | TIMESTAMPTZ | ✅ | NOW() | 生成时间 |
| expire_at | TIMESTAMPTZ | - | - | 过期时间(默认 NULL=永久) |

**索引**:`idx_redeem_codes_status` ON (status)

**兑换流程**:
1. 用户输入明文
2. 后端计算 SHA-256,查 `code_hash` 找到记录
3. 校验 `status = 'unused'` 且 `expire_at > NOW()`
4. UPDATE: status='used', used_by=用户ID, used_at=NOW()
5. 给用户加积分(走 point_accounts + point_transactions)

---

## 7. resume_files (简历文件)

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| user_id | BIGINT | ✅ | - | 用户 ID |
| type | VARCHAR(20) | ✅ | - | uploaded/generated |
| file_name | VARCHAR(255) | ✅ | - | 文件名 |
| file_format | VARCHAR(20) | ✅ | - | docx(只支持) |
| file_url | VARCHAR(512) | - | - | OSS URL |
| file_size | INT | - | - | 字节数 |
| content_text | TEXT | - | - | 解析后纯文本 |
| content_json | JSONB | - | - | 解析后结构化(段落/标题) |
| title | VARCHAR(255) | - | - | 简历标题(用于生成文件) |
| with_jd | BOOLEAN | ✅ | false | 是否含 JD |
| jd_text | TEXT | - | - | JD 文本(若 with_jd) |
| is_deleted | BOOLEAN | ✅ | false | 软删除 |
| created_at | TIMESTAMPTZ | ✅ | NOW() | 上传时间 |

**索引**:
- `idx_resume_files_user` ON (user_id, created_at DESC)
- `idx_resume_files_user_active` ON (user_id, is_deleted)

**生命周期**:**保留 1 年**,1 年后清理(可调整)

---

## 8. rewrite_records (改写记录)

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | BIGSERIAL | ✅ | auto | 主键 |
| user_id | BIGINT | ✅ | - | 用户 ID |
| feature | VARCHAR(50) | ✅ | - | partial_rewrite/full_rewrite/full_rewrite_with_jd |
| source_file_id | BIGINT | - | - | 源简历文件 ID |
| input_text | TEXT | - | - | 输入文本(部分改写时) |
| jd_text | TEXT | - | - | JD 文本(若带 JD) |
| title | VARCHAR(50) | - | - | 改写目标(完整改写时) |
| style_hint | VARCHAR(100) | - | - | 风格提示 |
| generated_file_id | BIGINT | - | - | 生成的文件 ID |
| output_text | TEXT | - | - | 改写输出 |
| improvement_points | JSONB | - | - | 5 条优化点 |
| points_cost | INT | ✅ | - | 消耗积分数 |
| point_transaction_id | BIGINT | - | - | 关联积分流水 |
| model_name | VARCHAR(50) | - | - | 调用的模型 |
| input_tokens | INT | - | - | 输入 token |
| output_tokens | INT | - | - | 输出 token |
| duration_ms | INT | - | - | 改写耗时(毫秒) |
| created_at | TIMESTAMPTZ | ✅ | NOW() | - |

**索引**:
- `idx_rewrite_records_user_created` ON (user_id, created_at DESC)
- `idx_rewrite_records_user_feature` ON (user_id, feature, created_at DESC)

**feature 取值**:
- `partial_rewrite`: 部分改写(50 积分)
- `full_rewrite`: 完整改写(1000 积分)
- `full_rewrite_with_jd`: 完整改写含 JD(1500 积分)

**生命周期**:**保留 2 年**,2 年后归档

---

## 9. system_configs (系统配置)

> **key-value 存储**,所有可变业务参数都从这读,允许后台可视化配置 + 热更新。

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| config_key | VARCHAR(100) | ✅ | - | 主键 |
| config_value | TEXT | ✅ | - | 值(可 JSON) |
| description | TEXT | - | - | 说明(中文) |
| updated_at | TIMESTAMPTZ | ✅ | NOW() | - |

**33 项关键配置**(见 `db/02_seed.sql`):

| key | value | 说明 |
|-----|-------|------|
| `points.partial_rewrite` | 50 | 部分改写扣分 |
| `points.full_rewrite` | 1000 | 完整改写扣分 |
| `points.full_rewrite_with_jd` | 1500 | 含 JD 完整改写扣分 |
| `trial.points` | 50 | 试用赠送积分 |
| `invitee.bonus.points` | 200 | 被推广奖励积分 |
| `commission.single` | 0.20 | 次卡返佣比例 |
| `commission.monthly` | 0.25 | 月卡返佣比例 |
| `commission.purchase` | 0.05 | 增购返佣比例 |
| `limit.partial_per_hour` | 10 | 部分改写每小时限次 |
| `limit.full_per_hour` | 3 | 完整改写每小时限次 |
| `limit.upload_per_day` | 20 | 上传每天限次 |
| `limit.sms_per_phone_per_day` | 10 | 短信每天限次 |
| `file.max_size_mb` | 10 | 文件大小上限 |
| `file.allowed_formats` | docx | 允许的格式 |
| `product.single.price` | 9.9 | 次卡价格 |
| `product.single.points` | 500 | 次卡积分 |
| `product.single.valid_days` | 30 | 次卡有效期(天) |
| `product.monthly.price` | 29 | 月卡价格 |
| `product.monthly.points` | 3000 | 月卡积分 |
| `product.monthly.valid_days` | 30 | 月卡有效期(天) |
| `product.points_1000.price` | 10 | 增购 1000 分价格 |
| `llm.model_name` | deepseek-chat | 默认模型 |
| `llm.max_input_tokens` | 8000 | 输入 token 上限 |
| `llm.max_output_tokens` | 4000 | 输出 token 上限 |
| `llm.temperature` | 0.5 | 温度 |
| `llm.timeout_seconds` | 60 | 超时(秒) |
| `sms.code_length` | 6 | 验证码长度 |
| `sms.code_ttl_seconds` | 300 | 验证码有效期 |
| `sms.resend_cooldown_seconds` | 60 | 重发冷却 |
| `jwt.access_token_expire_minutes` | 10080 | JWT 过期(7 天) |
| `withdraw.min_points` | 100 | 提现最小积分 |
| `withdraw.fee_rate` | 0 | 提现手续费率 |
| `promo.welcome_message` | 欢迎使用... | 欢迎语 |

---

## 全局约定

### 时间
- 所有时间字段用 `TIMESTAMPTZ`(带时区)
- 应用层统一 UTC 存储,展示时转 Asia/Shanghai

### ID
- 主键统一用 `BIGSERIAL`(自增 8 字节)
- 业务 ID(如订单号)用 `VARCHAR(32)`,带前缀

### 状态字段
- 用 `VARCHAR(20)` 而非 `ENUM`(便于扩展)
- 状态值用小写英文(active/paid/refunded)

### 软删除
- 用户、简历文件: `is_deleted` 或 `status='disabled'`
- 订单、改写记录: 硬删除(数量大,业务上不需要软删)

### 金额
- 全部用 `DECIMAL(10, 2)`,单位元
- 内部统计用 INT(分),避免浮点

### 索引策略
- 必有:`user_id` + `created_at DESC`
- 选择性高的:`phone`, `order_no`, `code_hash`
- 部分索引: `WHERE balance > 0`(避免空账户记录干扰)
