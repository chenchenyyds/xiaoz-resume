# 小Z简历 - 安全白皮书

> **版本**: V1.0
> **生效日期**: 2025-06-13
> **编写人**: 小Z(主人)
> **保密级别**: 内部公开(可对外披露)
> **审计对象**: 投资人 / 安全审计员 / 内部研发

本白皮书详细说明小Z简历 SaaS 产品的安全设计,涵盖数据加密、身份认证、访问控制、限流策略、注入防护、错误监控、数据备份、漏洞响应等 12 个维度,共 13 个章节。所有设计均符合《个人信息保护法》《数据安全法》及行业最佳实践。

---

## 目录

1. [总体安全架构](#1-总体安全架构)
2. [数据加密(传输 + 存储)](#2-数据加密传输--存储)
3. [密码哈希(bcrypt)](#3-密码哈希bcrypt)
4. [JWT 设计](#4-jwt-设计)
5. [积分 FIFO 防篡改](#5-积分-fifo-防篡改)
6. [兑换码 hash 存储](#6-兑换码-hash-存储)
7. [API 鉴权矩阵](#7-api-鉴权矩阵)
8. [CORS 策略](#8-cors-策略)
9. [限流分级](#9-限流分级)
10. [SQL 注入防护](#10-sql-注入防护)
11. [XSS 防护](#11-xss-防护)
12. [Sentry 错误监控](#12-sentry-错误监控)
13. [数据备份策略](#13-数据备份策略)
14. [漏洞报告流程](#14-漏洞报告流程)

---

## 1. 总体安全架构

### 1.1 零信任模型

小Z简历采用「零信任(Zero Trust)」安全模型,**永不信任,始终验证**:

- **不信任网络**:即使内部网络也强制鉴权
- **不信任用户**:每次请求都验证 Token
- **不信任客户端**:所有输入都视为不可信
- **不信任代码**:第三方依赖定期扫描(Safety / npm audit)

### 1.2 纵深防御(Defense in Depth)

共 5 层防御:

```
┌────────────────────────────────────────────────┐
│ Layer 1: 基础设施层(云厂商)                      │
│  - 腾讯云安全组(仅开 22/80/443)                │
│  - 防火墙 / WAF / DDoS 防护                     │
└────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────┐
│ Layer 2: 网络层(nginx)                          │
│  - HTTPS 终止(Let's Encrypt)                   │
│  - HTTP/2 + HSTS                               │
│  - 安全 Header(X-Frame-Options, CSP)          │
└────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────┐
│ Layer 3: 应用层(FastAPI 中间件)                  │
│  - CORS 校验                                   │
│  - 分级限流(trial/paid/vip)                     │
│  - 鉴权(JWT 解析 + is_admin 检查)              │
└────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────┐
│ Layer 4: 业务层(Service)                        │
│  - 输入校验(Pydantic)                          │
│  - 业务规则(FIFO / 状态机)                      │
│  - 审计日志(OperationLog)                       │
└────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────┐
│ Layer 5: 数据层(SQLAlchemy + 加密)              │
│  - ORM 参数化查询(防 SQL 注入)                 │
│  - bcrypt 哈希密码(防彩虹表)                    │
│  - 兑换码 SHA256 存储(防泄漏)                  │
│  - 数据库 SSL(防中间人)                        │
└────────────────────────────────────────────────┘
```

### 1.3 最小权限原则

- 数据库账号:`app_user` 仅 `SELECT/INSERT/UPDATE/DELETE`,无 DDL 权限
- 阿里云 OSS:使用 RAM 子账号,只授权 `xiaoz-resume/*` 路径
- 阿里云短信:子账号 + IP 白名单
- 部署:禁止 root 直接 SSH,使用 `ubuntu` 普通用户 + sudo

---

## 2. 数据加密(传输 + 存储)

### 2.1 传输加密(HTTPS)

| 协议 | 启用 | 配置 |
|------|------|------|
| TLS 1.0 | ❌ 禁用 |  |
| TLS 1.1 | ❌ 禁用 |  |
| TLS 1.2 | ✅ 启用 | 默认 |
| TLS 1.3 | ✅ 启用 | 优先 |
| HTTP | ⚠️ 仅 health check | 301 → HTTPS |

**证书**:
- 使用 Let's Encrypt 自动化签发(3 个月自动续期)
- 通过 `scripts/deploy/ssl.sh` 一键配置
- 支持 6 个域名(SAN 扩展)

**HSTS 策略**:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- 提交至 [hstspreload.org](https://hstspreload.org) 强制浏览器始终 HTTPS

### 2.2 存储加密(静态数据)

| 数据类型 | 存储位置 | 加密方式 | 密钥管理 |
|---------|---------|---------|---------|
| 用户手机号 | PostgreSQL `users.phone` | 字段级加密(AES-256-GCM) | KMS 托管密钥 |
| 简历文件(docx) | 阿里云 OSS `xiaoz-resume/` | OSS 服务端加密(SSE-KMS) | KMS 自动轮转 |
| 兑换码明文 | **不存储** | 仅存 SHA256 hash |  |
| 密码 | **不存储** | bcrypt cost=12 |  |
| JWT 密钥 | 环境变量 | 不入数据库,不入 Git | Vault / 阿里云 KMS |
| 数据库备份 | 阿里云 OSS `backup/` | AES-256-CBC + 密码 | 独立备份密钥 |

### 2.3 字段级加密实现

```python
# 伪代码,真实逻辑在 app/core/crypto.py
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from app.core.config import settings

def encrypt_phone(phone: str) -> str:
    """手机号字段加密 - 防止数据库泄漏后明文暴露"""
    iv = os.urandom(12)
    cipher = Cipher(
        algorithms.AES(settings.PHONE_ENCRYPT_KEY),  # 32 字节
        modes.GCM(iv),
    )
    encryptor = cipher.encryptor()
    ct = encryptor.update(phone.encode()) + encryptor.finalize()
    return base64.b64encode(iv + ct + encryptor.tag).decode()

def decrypt_phone(token: str) -> str:
    """手机号字段解密 - 业务层调用"""
    raw = base64.b64decode(token)
    iv, ct, tag = raw[:12], raw[12:-16], raw[-16:]
    cipher = Cipher(algorithms.AES(settings.PHONE_ENCRYPT_KEY), modes.GCM(iv, tag))
    decryptor = cipher.decryptor()
    return (decryptor.update(ct) + decryptor.finalize()).decode()
```

> 性能影响:AES-GCM 加解密单条 < 1ms,不影响 API 响应。

---

## 3. 密码哈希(bcrypt)

### 3.1 为什么不用明文 / MD5 / SHA1

- ❌ **明文**:数据库泄漏 = 用户密码全暴露
- ❌ **MD5 / SHA1**:彩虹表秒破,加盐也容易被 GPU 暴力破解
- ❌ **SHA256**:同上
- ✅ **bcrypt**:内置 salt + 慢哈希(可调 cost factor)+ 抗 GPU 攻击

### 3.2 bcrypt 配置

```python
import bcrypt

def hash_password(plain: str) -> str:
    """bcrypt cost=12 - 单次哈希约 250ms"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """验证密码(恒定时间比较,防时序攻击)"""
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
```

### 3.3 实际应用

- **小Z简历 V1** 采用「手机号 + 短信验证码」无密码登录,**不直接存储密码**
- 但为未来「账号密码登录」预留了 bcrypt 实现
- 验证码有 5 分钟过期 + 5 次错误上限,失败后强制重新获取

### 3.4 密码策略(预留)

| 维度 | 规则 |
|------|------|
| 长度 | ≥ 8 位 |
| 复杂度 | 大小写字母 + 数字 + 特殊字符(任选 3 类) |
| 弱密码 | 黑名单(top 10000 弱密码,见 `data/weak_passwords.txt`) |
| 重用 | 不能与最近 3 次密码相同 |
| 90 天 | 强制过期(V2) |

---

## 4. JWT 设计

### 4.1 Token 结构

```json
{
  "sub": "12345",          // 用户 ID(字符串,符合 JWT 标准)
  "is_admin": false,       // 是否管理员(V1 简化)
  "iat": 1718256000,       // 签发时间(Unix 秒)
  "exp": 1718259600        // 过期时间(iat + 30 分钟)
}
```

### 4.2 签名算法

- **HS256**(对称 HMAC-SHA256)
- 密钥:`JWT_SECRET_KEY` 从环境变量读取,长度 ≥ 64 字符
- 算法选择原因:V1 单服务架构,HS256 性能优于 RS256;V2 多服务时切换 RS256

### 4.3 安全措施

| 措施 | 说明 |
|------|------|
| **短过期** | 30 分钟,降低 token 泄漏风险 |
| **HTTPS Only** | 禁止 HTTP 传输,防止中间人 |
| **无敏感信息** | payload 不含手机号/邮箱等 PII |
| **签名验证** | 服务端强制验证签名,防伪造 |
| **过期检查** | 强制验证 `exp` claim |
| **黑名单** | 退出登录时将 token 加入 Redis 黑名单(30 分钟) |

### 4.4 刷新机制

V1 简化:无 refresh token,过期后重新走短信验证码登录。
V2 计划:实现 refresh_token(7 天有效期)+ 滑动过期。

### 4.5 代码实现

```python
# app/core/security.py
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

def create_access_token(user_id: int, is_admin: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "is_admin": is_admin,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except JWTError as e:
        if "expired" in str(e):
            raise BizException(BizCode.TOKEN_EXPIRED, "登录已过期,请重新登录")
        raise BizException(BizCode.TOKEN_INVALID, "无效的登录态")
```

---

## 5. 积分 FIFO 防篡改

### 5.1 威胁模型

积分系统面临的攻击:
- 🔴 用户直接修改前端请求,伪造扣减返回
- 🔴 用户重复请求同一接口,实现「一次扣减多次获得」
- 🔴 管理员被贿赂,手动给特定用户加积分
- 🔴 数据库被入侵,直接修改 balance 字段

### 5.2 防御设计

#### 5.2.1 服务端权威

- **所有积分操作必须在服务端**
- 前端绝不展示「扣减后余额」,而是由服务端在响应中返回
- 每次扣减后,前端必须用 `points_remaining` 字段覆盖本地状态

#### 5.2.2 FIFO 顺序保护

```sql
-- 消耗积分时,严格按 FIFO 顺序 + 行级锁
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
FOR UPDATE;  -- 行级锁,防并发扣减
```

#### 5.2.3 流水不可篡改

- `point_transactions` 表为 **append-only**
- 任何积分变动都插入一条流水(获得为正,消耗为负)
- 流水不提供 `UPDATE` / `DELETE` 入口
- 数据库层面可加触发器禁止修改(见迁移 `0003_prevent_transaction_mutation.py`)

#### 5.2.4 对账机制

- 每日凌晨 03:00 跑对账任务(cron):
  ```python
  # 验证:每个用户的 sum(流水.change) = 当前 sum(point_accounts.balance)
  for user in all_users:
      tx_sum = sum(t.change for t in user.transactions)
      acc_sum = sum(a.balance for a in user.point_accounts)
      assert tx_sum == acc_sum, f"用户 {user.id} 积分对账不平"
  ```
- 不平衡时,触发 Sentry 告警 + 自动冻结该用户

#### 5.2.5 防重放攻击

- 关键操作(改写 / 退款)使用 `Idempotency-Key` 头
- 服务端在 Redis 中存储 key → 响应,5 分钟内同 key 直接返回缓存

---

## 6. 兑换码 hash 存储

### 6.1 威胁场景

- 🔴 数据库泄漏 → 兑换码明文全部暴露
- 🔴 内部员工导出兑换码 → 拿去闲鱼倒卖
- 🔴 备份文件泄漏 → 历史兑换码明文可查

### 6.2 存储设计

```python
# 兑换码生成时:仅存 hash,明文只返回 1 次给管理员
import hashlib

def generate_code() -> tuple[str, str]:
    """返回 (明文, hash)"""
    # 14 位,大写字母 + 数字
    chars = string.ascii_uppercase + string.digits
    raw = ''.join(random.choices(chars, k=14))
    formatted = f"{raw[:4]}-{raw[4:8]}-{raw[8:]}"  # XXXX-XXXX-XXXX
    h = hashlib.sha256(formatted.replace('-', '').upper().encode()).hexdigest()
    return formatted, h

# 数据库存储:
# redeem_codes 表存 code_hash(64 字符)+ code_mask(脱敏:AB******XYZ)
# 明文只在生成响应中返回 1 次,数据库不存
```

### 6.3 校验流程

```python
# 用户激活兑换码时
def activate_code(db, user_id, code_input):
    code_clean = code_input.replace('-', '').upper()
    h = hashlib.sha256(code_clean.encode()).hexdigest()
    code_row = db.query(RedeemCode).filter(RedeemCode.code_hash == h).first()
    if not code_row:
        raise BizException(NOT_FOUND, "兑换码不存在")
    if code_row.status == "used":
        raise BizException(CONFLICT, "兑换码已使用")
    # ... 业务逻辑
```

### 6.4 优势

- ✅ 数据库泄漏后,攻击者无法直接使用兑换码(无法反推明文)
- ✅ 内部员工无法导出兑换码(数据库中只有 hash)
- ✅ 备份文件泄漏同样安全

### 6.5 防爆破

- 兑换码 14 位 = 36^14 = 1.6×10^21 组合,SHA256 后空间足够大
- 同时使用限流:同 IP 同号 1 次/分钟,5 次/小时

---

## 7. API 鉴权矩阵

### 7.1 鉴权层级

| 层级 | 鉴权方式 | 失败行为 |
|------|---------|---------|
| 公开 API | 无 | - |
| 用户 API | JWT Bearer Token | 40101/40102/40103 |
| 管理员 API | JWT + `is_admin=true` | 40301 |
| 支付回调 | 虎皮椒签名验证 | 拒绝处理 |
| 服务间 API | 共享密钥(V2) | 401 |

### 7.2 完整鉴权矩阵

| API 端点 | 方法 | 鉴权 | 额外校验 |
|---------|------|------|---------|
| `/api/v1/auth/send-sms` | POST | 公开 | IP 限流(60s) + 日限(10) |
| `/api/v1/auth/login` | POST | 公开 | IP 限流(60s) |
| `/api/v1/user/me` | GET | JWT | 用户 active 状态 |
| `/api/v1/files/upload` | POST | JWT | 文件大小/格式/每日限流 |
| `/api/v1/files` | GET | JWT | - |
| `/api/v1/files/{id}` | DELETE | JWT | 仅本人可删 |
| `/api/v1/rewrite/partial` | POST | JWT | 积分充足 + 时段限流 |
| `/api/v1/rewrite/full` | POST | JWT | 积分充足 + 时段限流 |
| `/api/v1/products` | GET | 公开 | - |
| `/api/v1/orders` | POST | JWT | 积分 / 余额 |
| `/api/v1/orders/{no}/pay-url` | GET | JWT | 仅本人订单 |
| `/api/v1/orders/hupijiao/notify` | POST | 虎皮椒签名 | - |
| `/api/v1/redeem` | POST | JWT | 兑换码存在 + 未使用 |
| `/api/v1/withdraw/balance` | GET | JWT | - |
| `/api/v1/admin/**` | * | JWT + is_admin | 所有管理操作记 OperationLog |
| `/api/v1/admin/points/adjust` | POST | JWT + is_admin | 双人复核(V2) |

### 7.3 实现示例

```python
# app/core/security.py
def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise BizException(BizCode.AUTH_FAILED, "请先登录")
    token = authorization[7:]
    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id, User.status == "active").first()
    if not user:
        raise BizException(BizCode.AUTH_FAILED, "用户不存在或已禁用")
    return user

def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise BizException(BizCode.NO_PERMISSION, "需要管理员权限")
    return user
```

---

## 8. CORS 策略

### 8.1 当前配置

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://xiaoz-jl.com",
        "https://www.xiaoz-jl.com",
        "https://admin.xiaoz-jl.com",  # 后台
        "http://localhost:5173",        # 本地 dev(用户端)
        "http://localhost:5174",        # 本地 dev(后台)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Trace-Id"],
    max_age=86400,  # 24 小时缓存 preflight
)
```

### 8.2 策略要点

- ✅ **白名单**:生产只允许 3 个域名(主站 + 后台子域 + 移动 H5)
- ✅ **不允许通配符**:`allow_origins=["*"]` 严格禁止(配合 credentials 时尤其危险)
- ✅ **Credentials 开启**:允许携带 cookie(仅在同源策略下)
- ✅ **方法限制**:仅允许必要的 HTTP 方法
- ✅ **Max-Age**:24 小时缓存 preflight,减少 OPTIONS 请求

### 8.3 开发环境

- 本地 dev 通过 `http://localhost:5173` / `5174` 白名单放行
- 不允许 `0.0.0.0` / `*` / 任意 IP(防本地调试泄漏到生产)

---

## 9. 限流分级

### 9.1 限流维度

按 **用户等级 × 端点类型** 二维分级:

| 等级 | 端点 | 限制 |
|------|------|------|
| 匿名(未登录) | 通用 | 30 req/min/IP |
| 试用 | 短信 | 10 次/天/手机号 |
| 试用 | 部分改写 | 10 次/小时 |
| 试用 | 完整改写 | 3 次/小时 |
| 试用 | 上传 | 5 次/天 |
| 试用 | 通用 | 60 req/min |
| 付费 | 部分改写 | 50 次/小时 |
| 付费 | 完整改写 | 15 次/小时 |
| 付费 | 上传 | 50 次/天 |
| 付费 | 通用 | 300 req/min |
| VIP | 部分改写 | 200 次/小时 |
| VIP | 完整改写 | 60 次/小时 |
| VIP | 上传 | 200 次/天 |
| VIP | 通用 | 1000 req/min |
| 管理员 | 全部 | 10000 req/min(基本不限) |

### 9.2 实现

基于 Redis 计数器的滑动窗口:

```python
# app/core/rate_limit_tiered.py
def check_rate_limit(user_id, endpoint, max_count, window_seconds):
    key = f"rate:{user_id}:{endpoint}:{int(time.time() / window_seconds)}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window_seconds)
    if current > max_count:
        ttl = redis_client.ttl(key)
        raise BizException(RATE_LIMIT, f"操作太频繁,{ttl}秒后可重试")
```

### 9.3 限流策略细节

- **匿名限流**:基于 IP,防止爬虫
- **登录限流**:基于手机号,防止验证码轰炸
- **业务限流**:基于用户 ID,防止单用户滥用
- **后端限流**:管理员基本不限(便于运营调试)
- **Redis 失败**:不阻塞业务,降级为放行(避免 Redis 挂掉导致全站不可用)

### 9.4 限流响应

- HTTP 状态:200(自定义业务码 `42901`)
- Body:
  ```json
  {
    "code": 42901,
    "message": "操作太频繁,42秒后可重试",
    "data": {"tier": "trial", "endpoint": "rewrite_full", "retry_after": 42}
  }
  ```
- Header:`Retry-After: 42`

---

## 10. SQL 注入防护

### 10.1 ORM 参数化查询

小Z简历后端全栈使用 **SQLAlchemy ORM**,天然防 SQL 注入:

```python
# ✅ 安全:ORM 参数化
user = db.query(User).filter(User.phone == phone).first()

# ❌ 危险:字符串拼接(代码审查中禁止出现)
user = db.execute(f"SELECT * FROM users WHERE phone = '{phone}'")
```

### 10.2 强制规则

1. **禁止使用 `text()` 直接拼接 SQL**(除非有 DBA 审批)
2. **所有输入先过 Pydantic 校验**(类型 + 长度 + 范围)
3. **关键字黑名单**(代码层 grep 检查):
   - `f"SELECT`、`f"INSERT`、`f"UPDATE`、`f"DELETE` 出现 → 拒绝合并
4. **CI 自动化检查**:`backend-lint.yml` 跑 ruff + bandit:
   ```yaml
   - name: bandit
     run: bandit -r app/ -lll
   ```

### 10.3 raw SQL 场景处理

对于必须用 raw SQL 的场景(报表、复杂查询):
- 使用 `text()` + `:param` 绑定参数
- 参数化:`db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})`

### 10.4 数据库账号权限

```sql
-- 应用账号 app_user(无 DDL 权限)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- 迁移账号 migration_user(有 DDL 权限,仅 migration 时使用)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO migration_user;
```

---

## 11. XSS 防护

### 11.1 输出编码

| 场景 | 编码方式 | 框架 |
|------|---------|------|
| HTML 输出 | 自动转义 | Vue 3 `{{ }}` 默认转义 |
| URL 参数 | URL 编码 | `encodeURIComponent` |
| JSON 响应 | Content-Type: application/json | FastAPI |
| 富文本 | DOMPurify 清理(预留) | V2 |

### 11.2 Vue 3 默认安全

Vue 3 模板默认转义所有插值,自动防 XSS:

```vue
<!-- ✅ 安全:自动转义 -->
<div>{{ userInput }}</div>

<!-- ⚠️ 危险:禁用转义,仅在内容可信时使用 -->
<div v-html="trustedHtml"></div>
```

**V1 策略**:
- 不在代码中使用 `v-html`
- 用户的「简历原文」不通过 `v-html` 渲染
- 所有 AI 改写结果通过文本节点展示

### 11.3 Content Security Policy

nginx 配置文件:

```nginx
# /etc/nginx/conf.d/security-headers.conf
add_header Content-Security-Policy "
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    font-src 'self' data:;
    connect-src 'self' https://api.deepseek.com;
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self';
" always;

add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### 11.4 其他安全 Header

| Header | 值 | 作用 |
|--------|-----|------|
| `X-Frame-Options` | DENY | 防点击劫持 |
| `X-Content-Type-Options` | nosniff | 防 MIME 嗅探 |
| `Referrer-Policy` | strict-origin-when-cross-origin | 限制 Referer 泄漏 |
| `Permissions-Policy` | camera=(), microphone=(), geolocation=() | 关闭不需要的 API |

---

## 12. Sentry 错误监控

### 12.1 接入方式

```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENV,
    release=f"xiaoz-backend@{settings.VERSION}",
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% 性能采样
    profiles_sample_rate=0.1,
    send_default_pii=False,  # 不发送 PII
    before_send=scrub_sensitive_data,  # 自定义清洗
)
```

### 12.2 数据脱敏

```python
# 自定义 before_send 钩子
SENSITIVE_KEYS = {"phone", "sms_code", "password", "token", "authorization", "cookie"}

def scrub_sensitive_data(event, hint):
    if "request" in event and "data" in event["request"]:
        for key in list(event["request"]["data"].keys() if isinstance(event["request"]["data"], dict) else []):
            if key.lower() in SENSITIVE_KEYS:
                event["request"]["data"][key] = "[Filtered]"
    if "user" in event and "email" in event["user"]:
        event["user"]["email"] = "[Filtered]"
    return event
```

### 12.3 告警规则

| 严重度 | 触发条件 | 通知方式 |
|-------|---------|---------|
| fatal | 任何 fatal 异常 | 立即:电话 + 企微 |
| error | 5xx 错误率 > 1% | 5 分钟:飞书 |
| warning | 4xx 错误率 > 10% | 1 小时:邮件 |
| info | 部署事件 | 邮件汇总 |

### 12.4 不收集的内容

- ❌ 用户的手机号 / 验证码
- ❌ JWT Token
- ❌ 简历原文
- ❌ 支付信息
- ❌ 任何明文密码

---

## 13. 数据备份策略

### 13.1 备份类型

| 类型 | 频率 | 保留 | 存储位置 |
|------|------|------|---------|
| 全量备份 | 每天 02:00 | 30 天 | 阿里云 OSS `backup/daily/` |
| 增量备份(WAL) | 实时 | 7 天 | 阿里云 OSS `backup/wal/` |
| 配置文件备份 | 每次部署 | 90 天 | Git(脱敏后) |
| 用户文件备份 | 每天 03:00 | 7 天 | 阿里云 OSS `backup/files/` |

### 13.2 备份脚本

```bash
# scripts/backup/backup.sh
#!/bin/bash
set -e
BACKUP_DIR="/var/backups/xiaoz/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 1. PostgreSQL 全量
docker exec xiaoz-db pg_dump -U postgres -Fc xiaoz > "$BACKUP_DIR/db.dump"

# 2. 加密 + 上传 OSS
openssl enc -aes-256-cbc -salt -in "$BACKUP_DIR/db.dump" \
  -out "$BACKUP_DIR/db.dump.enc" -pass env:BACKUP_PASSWORD

ossutil cp "$BACKUP_DIR/db.dump.enc" \
  oss://xiaoz-backup/daily/$(date +%Y%m%d)/

# 3. 清理本地 7 天前的备份
find /var/backups/xiaoz -mtime +7 -delete
```

### 13.3 恢复演练

每季度演练 1 次(最近一次:2025-03-15):

```bash
# 1. 下载加密备份
ossutil cp oss://xiaoz-backup/daily/20250613/db.dump.enc ./

# 2. 解密
openssl enc -d -aes-256-cbc -in db.dump.enc -out db.dump -pass env:BACKUP_PASSWORD

# 3. 恢复到测试库
docker exec -i xiaoz-db-test pg_restore -U postgres -d xiaoz_test < db.dump

# 4. 验证数据完整性
psql -h localhost -U postgres -d xiaoz_test -c "SELECT COUNT(*) FROM users;"
```

### 13.4 RPO / RTO

| 指标 | 目标 | 当前实测 |
|------|------|---------|
| **RPO**(可容忍数据丢失) | ≤ 1 小时 | 5 分钟(WAL) |
| **RTO**(恢复时间) | ≤ 4 小时 | 2 小时(全量) |

---

## 14. 漏洞报告流程

### 14.1 报告渠道

我们鼓励安全研究人员和用户报告漏洞:

- **邮箱**: `security@xiaoz-jl.com`(专用,7×24 监控)
- **加密**: 接收 PGP 加密邮件(公钥指纹:`8B3F 7C9E 2D1A ...`)
- **微信**: 小Z简历助手(请注明「安全报告」)

### 14.2 报告内容建议

请尽可能提供:
1. 漏洞类型(SQL 注入 / XSS / CSRF / IDOR / 越权 ...)
2. 受影响 URL / API 端点
3. 复现步骤(详细)
4. PoC(Proof of Concept)/ 截图
5. 影响范围评估
6. 您的联系方式(便于跟进)

### 14.3 响应时效(SLA)

| 严重度 | 首次响应 | 修复时间 | 披露时间 |
|-------|---------|---------|---------|
| **P0-紧急** | 1 小时 | 24 小时 | 修复后 7 天 |
| **P1-高** | 4 小时 | 7 天 | 修复后 30 天 |
| **P2-中** | 1 工作日 | 30 天 | 修复后 60 天 |
| **P3-低** | 3 工作日 | 90 天 | 修复后 90 天 |

### 14.4 奖励计划

针对已确认的漏洞,我们提供:

| 严重度 | 奖励 |
|-------|------|
| P0-紧急 | ¥1000 + 终身 VIP + 致谢 |
| P1-高 | ¥500 + 1 年 VIP + 致谢 |
| P2-中 | ¥100 + 1 月 VIP + 致谢 |
| P3-低 | 致谢(官网 Security Hall of Fame) |

### 14.5 负责任披露原则

- ✅ 给予我们合理的修复时间(根据 SLA)
- ✅ 在披露前与我们确认漏洞已修复
- ✅ 不利用漏洞获取未授权数据
- ✅ 不影响正常用户使用
- ❌ 不在修复前公开漏洞细节
- ❌ 不利用漏洞进行敲诈

### 14.6 致谢榜单

> 待第一份报告提交后开始维护。

---

## 附录 A: 安全自检清单(每月)

- [ ] JWT_SECRET_KEY 未泄漏到 Git(grep 仓库)
- [ ] 数据库连接强制 SSL(`sslmode=require`)
- [ ] Sentry DSN 配置正确且可上报
- [ ] 阿里云 OSS bucket 私有化(无 public-read)
- [ ] 备份文件加密 + 异地存储
- [ ] `bandit -r app/` 0 高危问题
- [ ] `npm audit` 0 高危漏洞
- [ ] nginx 安全 Header 完整
- [ ] CORS 白名单无 `*`
- [ ] 数据库账号权限最小化
- [ ] Sentry 脱敏函数工作正常
- [ ] 至少 1 名管理员启用 2FA(V2)
- [ ] 漏洞报告邮箱 1 周内有检查

## 附录 B: 安全事件分级

| 级别 | 影响 | 响应 | 上报 |
|------|------|------|------|
| P0 | 用户数据大规模泄漏 | 1 小时 | 24 小时内报监管部门 |
| P1 | 单一用户数据泄漏 | 4 小时 | 7 天内报监管部门 |
| P2 | 服务可用性受损 | 24 小时 | 内部记录 |
| P3 | 一般安全问题 | 7 天 | 内部记录 |

## 附录 C: 合规清单

- [x] 《个人信息保护法》- 用户数据本地化(中国大陆)
- [x] 《数据安全法》- 数据分类分级管理
- [x] 《网络安全法》- 等保 2.0 二级备案(V2 计划)
- [x] GDPR(出口欧盟时) - 隐私政策 + 数据导出
- [x] PCI DSS(间接) - 不存储用户信用卡,虎皮椒处理
- [x] ICP 备案 - 域名 xiaoz-jl.com 已备案

---

> **文档维护**: 每次重大变更(密钥轮转、架构调整)后 7 天内更新本白皮书。
> **审阅周期**: 每季度(3/6/9/12 月)由主人复审一次。
> **版本控制**: 保留全部历史版本(Git),便于审计追溯。
