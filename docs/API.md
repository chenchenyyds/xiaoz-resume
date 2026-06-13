# 小Z简历 - API 文档

> **版本**: V1.0
> **最后更新**: 2025-06-13
> **Base URL**: `https://xiaoz-jl.com/api/v1`
> **数据格式**: JSON (UTF-8)
> **鉴权方式**: JWT Bearer Token
> **在线文档**: https://xiaoz-jl.com/api/docs (Swagger UI)

本目录收录小Z简历 SaaS 产品的全部 **30 个 API 端点**(用户端 13 + 后台 17),含路径、方法、鉴权、请求/响应示例、错误码。所有响应均采用统一业务码格式 `{code, message, data}`,`code=0` 表示成功。

---

## 目录

### 用户端 API(13 个)
1. [鉴权(2)](#1-鉴权-2-个)
   - [POST /auth/send-sms](#11-post-authsend-sms发送验证码)
   - [POST /auth/login](#12-post-authlogin登录注册)
2. [用户信息(1)](#2-用户信息-1-个)
   - [GET /user/me](#21-get-userme我的信息)
3. [文件(3)](#3-文件-3-个)
   - [POST /files/upload](#31-post-filesupload上传简历)
   - [GET /files](#32-get-files我的文件列表)
   - [DELETE /files/{file_id}](#33-delete-filesfile_id删除文件)
4. [改写(2)](#4-改写-2-个)
   - [POST /rewrite/partial](#41-post-rewritepartial部分改写)
   - [POST /rewrite/full](#42-post-rewritefull完整改写)
5. [商品 / 订单(4)](#5-商品--订单-4-个)
   - [GET /products](#51-get-products商品列表)
   - [POST /orders](#52-post-orders创建订单)
   - [GET /orders/{order_no}/pay-url](#53-get-ordersorder_nopay-url获取支付链接)
   - [POST /orders/hupijiao/notify](#54-post-ordershupijiaonotify支付回调)
6. [兑换码 / 提现(2)](#6-兑换码--提现-2-个)
   - [POST /redeem](#61-post-redeem激活兑换码)
   - [GET /withdraw/balance](#62-get-withdrawbalance我的可提现余额)

### 后台 API(17 个)
7. [数据看板(1)](#7-数据看板-1-个)
   - [GET /admin/dashboard/overview](#71-get-admindashboardoverview看板概览)
8. [订单管理(3)](#8-订单管理-3-个)
   - [GET /admin/orders](#81-get-adminorders订单列表)
   - [GET /admin/orders/{order_no}](#82-get-adminordersorder_no订单详情)
   - [POST /admin/orders/{order_no}/refund](#83-post-adminordersorder_norefund退款)
9. [兑换码管理(4)](#9-兑换码管理-4-个)
   - [POST /admin/codes/generate](#91-post-admincodesgenerate批量生成)
   - [GET /admin/codes](#92-get-admincodes兑换码列表)
   - [POST /admin/codes/{code_id}/revoke](#93-post-admincodescode_idrevoke作废)
   - [GET /admin/codes/export](#94-get-admincodesexport导出-csv)
10. [用户管理(4)](#10-用户管理-4-个)
    - [GET /admin/users](#101-get-adminusers用户列表)
    - [GET /admin/users/{user_id}](#102-get-adminusersuser_id用户详情)
    - [POST /admin/users/{user_id}/disable](#103-post-adminusersuser_iddisable禁用)
    - [POST /admin/users/{user_id}/enable](#104-post-adminusersuser_idenable启用)
    - [POST /admin/users/{user_id}/adjust-points](#105-post-adminusersuser_idadjust-points调整积分)
11. [积分流水(2)](#11-积分流水-2-个)
    - [GET /admin/points/transactions](#111-get-adminpointstransactions积分流水)
    - [GET /admin/points/stats](#112-get-adminpointsstats流水统计)
    - [POST /admin/points/adjust](#113-post-adminpointsadjust管理员调账)
12. [操作日志(2)](#12-操作日志-2-个)
    - [GET /admin/logs](#121-get-adminlogs操作日志)
    - [GET /admin/logs/stats](#122-get-adminlogsstats日志统计)

### 附录
- [通用响应格式](#通用响应格式)
- [错误码表](#错误码表)
- [鉴权说明](#鉴权说明)

---

## 通用响应格式

所有 API 响应统一格式:

```json
{
  "code": 0,
  "message": "ok",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 业务码,0=成功,其他=失败 |
| `message` | string | 人类可读的提示信息 |
| `data` | object/null | 业务数据(成功时)或附加信息(失败时) |

> 注意: HTTP 状态码始终返回 200,真正的错误通过业务码 `code` 区分。

---

## 错误码表

| 业务码 | HTTP | 含义 | 客户端处理 |
|-------|------|------|-----------|
| 0 | 200 | 成功 | 解析 data |
| 40001 | 200 | 参数错误 | 检查请求参数 |
| 40101 | 200 | 未登录 | 跳转到登录页 |
| 40102 | 200 | Token 过期 | 跳转到登录页 |
| 40103 | 200 | Token 无效 | 跳转到登录页 |
| 40301 | 200 | 无权限 | 提示用户 |
| 40401 | 200 | 资源不存在 | 提示用户 |
| 40901 | 200 | 状态冲突 | 重新拉取状态 |
| 41001 | 200 | 积分不足 | 引导充值 |
| 42901 | 200 | 限流 | 等待后重试 |
| 50001 | 200 | 支付错误 | 联系客服 |
| 50002 | 200 | 短信错误 | 重试 |
| 50003 | 200 | LLM 错误 | 重试或换 prompt |
| 50004 | 200 | OSS 错误 | 重试 |
| 50000 | 200 | 服务器异常 | 联系客服 |

---

## 鉴权说明

### 用户端鉴权

除 `auth/*` 和 `products` 外,所有用户端 API 都需要 JWT:

```
Authorization: Bearer <jwt_token>
```

JWT 包含 4 个 claim:
- `sub`:用户 ID
- `is_admin`:是否管理员
- `iat`:签发时间
- `exp`:过期时间(30 分钟)

### 后台鉴权

所有 `/admin/*` 需要:
1. JWT
2. `is_admin=true`

后台 API 强制记录 `OperationLog`,便于审计。

---

## 1. 鉴权(2 个)

### 1.1 POST /auth/send-sms(发送验证码)

**鉴权**: 公开  
**限流**: 同号 60s 1 次 + 每日 10 次

#### 请求

```http
POST /api/v1/auth/send-sms
Content-Type: application/json

{
  "phone": "13800000000"
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "sent": true,
    "dev_code": "123456"  // 仅开发模式返回,生产为 null
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | 手机号格式错误 |
| 42901 | 60s 内重复 / 今日已超 10 次 |

---

### 1.2 POST /auth/login(登录/注册)

**鉴权**: 公开  
**限流**: 60s 1 次

#### 请求

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "phone": "13800000000",
  "code": "123456",
  "invite_code": "ABCD1234"  // 可选
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_id": 42,
    "is_new": false,
    "invite_code": "TEST0001"  // 用户的推广码
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | 缺少 phone 或 code |
| 40101 | 验证码错误或已过期 |

#### 副作用
- 新用户自动注册 + 生成 6-8 位 invite_code
- 若带 invite_code,双方各得 200 积分(下次)
- 试用积分 50 分(90 天过期)首次赠送

---

## 2. 用户信息(1 个)

### 2.1 GET /user/me(我的信息)

**鉴权**: 需要 JWT

#### 请求

```http
GET /api/v1/user/me
Authorization: Bearer <token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user": {
      "id": 42,
      "phone": "138****0000",
      "nickname": "小Z",
      "avatar_url": "https://oss.example.com/avatar/42.jpg",
      "invite_code": "TEST0001",
      "is_admin": false,
      "created_at": "2025-06-01T10:00:00Z"
    },
    "points": {
      "trial_balance": 50,
      "subscription_balance": 1200,
      "purchase_balance": 100,
      "total_balance": 1350
    }
  }
}
```

---

## 3. 文件(3 个)

### 3.1 POST /files/upload(上传简历)

**鉴权**: 需要 JWT  
**限流**: 试用 5/天,付费 50/天,VIP 200/天  
**文件类型**: 仅 `.docx`,最大 10MB

#### 请求

```http
POST /api/v1/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file=@resume.docx
title=我的简历
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "file_id": 123,
    "file_name": "resume.docx",
    "file_url": "https://oss.example.com/xiaoz-resume/42/20250613_xxx.docx",
    "file_size": 102400,
    "type": "uploaded"
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | 文件格式不是 docx |
| 40001 | 文件 > 10MB |
| 42901 | 今日上传超限 |

---

### 3.2 GET /files(我的文件列表)

**鉴权**: 需要 JWT

#### 请求

```http
GET /api/v1/files
Authorization: Bearer <token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 123,
        "file_name": "resume_2025.docx",
        "file_format": "docx",
        "file_url": "https://oss.example.com/.../xxx.docx",
        "file_size": 102400,
        "type": "uploaded",  // uploaded/generated
        "with_jd": false,
        "created_at": "2025-06-13T10:00:00Z"
      }
    ],
    "total": 1
  }
}
```

---

### 3.3 DELETE /files/{file_id}(删除文件)

**鉴权**: 需要 JWT(仅本人)

#### 请求

```http
DELETE /api/v1/files/123
Authorization: Bearer <token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "deleted": true,
    "file_id": 123
  }
}
```

> 注: V1 采用软删除(is_deleted=true),30 天后清理。

---

## 4. 改写(2 个)

### 4.1 POST /rewrite/partial(部分改写)

**鉴权**: 需要 JWT  
**限流**: 试用 10/h,付费 50/h,VIP 200/h  
**消耗**: 50 积分/次

#### 请求

```http
POST /api/v1/rewrite/partial
Authorization: Bearer <token>
Content-Type: application/json

{
  "text": "负责公司核心业务系统的开发和维护,参与过 3 个大型项目",
  "title": "工作经历",  // 可选
  "style_hint": "更专业"  // 可选
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "output_text": "主导电商平台核心业务系统的架构设计与开发,带领 5 人小组完成 3 个大型项目(累计交付 200+ 功能,服务 50 万 DAU)",
    "explanation": "补充了量化数据,使用动词「主导」提升主动性,增加了团队规模信息",
    "points_cost": 50,
    "points_remaining": 1300
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | text 字段 < 10 字 |
| 41001 | 积分不足 |
| 42901 | 时段限流 |
| 50003 | LLM 调用失败(自动重试 1 次) |

---

### 4.2 POST /rewrite/full(完整改写)

**鉴权**: 需要 JWT  
**限流**: 试用 3/h,付费 15/h,VIP 60/h  
**消耗**: 1000 积分(不含 JD)/ 1500 积分(含 JD)

#### 请求

```http
POST /api/v1/rewrite/full
Authorization: Bearer <token>
Content-Type: application/json

{
  "file_id": 123,
  "jd_text": "职位:Python 后端开发工程师\n要求:3 年以上 Python 经验...",  // 可选
  "style_hint": "突出技术深度"  // 可选
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "output_text": "张三 | 男 | 25 岁\n工作经历:...(完整改写后)",
    "improvement_points": [
      "补充了量化数据:用户量、QPS、节省成本",
      "调整动词时态,使用「主导/负责/推动」",
      "补充技术栈关键词(对应 JD)",
      "简化冗余表达,提升可读性"
    ],
    "file_url": "https://oss.example.com/.../rewrite_xxx.docx",  // 完整 docx 下载链接
    "points_cost": 1500,
    "points_remaining": -200  // 积分不足时的提示
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | file_id 不存在 |
| 40401 | 简历不存在或已删除 |
| 41001 | 积分不足 |
| 42901 | 时段限流 |

> `file_url` 有效期 7 天。

---

## 5. 商品 / 订单(4 个)

### 5.1 GET /products(商品列表)

**鉴权**: 公开

#### 请求

```http
GET /api/v1/products
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "code": "single",
        "name": "单次包",
        "description": "50 积分,30 天有效",
        "price": 9.9,
        "points": 50,
        "valid_days": 30,
        "point_type": "subscription"
      },
      {
        "code": "monthly",
        "name": "月卡",
        "description": "1200 积分,30 天有效",
        "price": 49,
        "points": 1200,
        "valid_days": 30,
        "point_type": "subscription"
      },
      {
        "code": "points_1000",
        "name": "增购 1000 积分",
        "description": "1000 积分,永久有效",
        "price": 99,
        "points": 1000,
        "valid_days": null,
        "point_type": "purchase"
      }
    ]
  }
}
```

---

### 5.2 POST /orders(创建订单)

**鉴权**: 需要 JWT

#### 请求

```http
POST /api/v1/orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_code": "monthly",
  "invite_code": "ABCD1234"  // 可选,推广人
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "order_no": "X20250613100000001",
    "amount": 49.00,
    "pay_url": "https://pay.xiaoz-jl.com/hupijiao/checkout/xxx"  // 虎皮椒支付链接
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | 商品代码不存在 |
| 40901 | 用户有未支付订单 |

---

### 5.3 GET /orders/{order_no}/pay-url(获取支付链接)

**鉴权**: 需要 JWT(仅本人)

#### 请求

```http
GET /api/v1/orders/X20250613100000001/pay-url
Authorization: Bearer <token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "pay_url": "https://pay.xiaoz-jl.com/hupijiao/checkout/yyy"
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40401 | 订单不存在 |
| 40901 | 订单状态非 pending,不可支付 |

---

### 5.4 POST /orders/hupijiao/notify(支付回调)

**鉴权**: 虎皮椒签名验证(无需 JWT)

> 虎皮椒以 Form 表单方式回调,服务端验证签名后处理订单。

#### 请求

```http
POST /api/v1/orders/hupijiao/notify
Content-Type: application/x-www-form-urlencoded

trade_order_id=X20250613100000001&...
```

#### 响应(文本)

```
success  // 处理成功
fail     // 处理失败(虎皮椒会重试)
```

---

## 6. 兑换码 / 提现(2 个)

### 6.1 POST /redeem(激活兑换码)

**鉴权**: 需要 JWT

#### 请求

```http
POST /api/v1/redeem
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "ABCD-EFGH-JKLM"
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "type": "monthly",   // single/monthly/purchase
    "points": 1200,
    "valid_days": 30,
    "code_id": 88
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40401 | 兑换码不存在 |
| 40901 | 兑换码已使用 / 已作废 |
| 40901 | 兑换码已过期 |

#### 副作用
- 兑换码标记为已使用,记录 user_id
- 积分按 type 写入 point_accounts 批次

---

### 6.2 GET /withdraw/balance(我的可提现余额)

**鉴权**: 需要 JWT

> V1 阶段返佣以积分形式发放,不打款,这里只展示数据。

#### 请求

```http
GET /api/v1/withdraw/balance
Authorization: Bearer <token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "commission_earned": 0,
    "withdrawn": 0,
    "available": 0,
    "note": "V1 阶段返佣以积分形式发放,不打款,可在下次消费时直接用"
  }
}
```

---

## 7. 数据看板(1 个)

### 7.1 GET /admin/dashboard/overview(看板概览)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/dashboard/overview
Authorization: Bearer <admin_token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total_users": 1250,
    "new_users_today": 18,
    "total_revenue_fen": 2450000,  // 24500 元
    "revenue_today_fen": 9900,     // 99 元
    "orders_today": 5,
    "active_users_today": 89
  }
}
```

---

## 8. 订单管理(3 个)

### 8.1 GET /admin/orders(订单列表)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/orders?status=paid&page=1&page_size=20
Authorization: Bearer <admin_token>
```

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | pending/paid/refunded/closed |
| product_code | string | 商品代码过滤 |
| page | int | 页码,默认 1 |
| page_size | int | 每页数量,默认 20,最大 100 |

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "order_no": "X20250613100000001",
        "user_id": 42,
        "user_phone": "138****0000",
        "product_code": "monthly",
        "amount": 49.00,
        "pay_amount": 49.00,
        "pay_channel": "hupijiao",
        "status": "paid",
        "invite_user_id": 7,
        "paid_at": "2025-06-13T10:05:23Z",
        "refunded_at": null,
        "refund_amount": null,
        "created_at": "2025-06-13T10:00:00Z"
      }
    ],
    "total": 250
  }
}
```

---

### 8.2 GET /admin/orders/{order_no}(订单详情)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/orders/X20250613100000001
Authorization: Bearer <admin_token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "order_no": "X20250613100000001",
    "user_id": 42,
    "user_phone": "13800000000",
    "product_code": "monthly",
    "amount": 49.00,
    "pay_amount": 49.00,
    "pay_channel": "hupijiao",
    "status": "paid",
    "invite_user_id": 7,
    "paid_at": "2025-06-13T10:05:23Z",
    "refunded_at": null,
    "refund_amount": null,
    "created_at": "2025-06-13T10:00:00Z"
  }
}
```

---

### 8.3 POST /admin/orders/{order_no}/refund(退款)

**鉴权**: 需要 JWT + is_admin  
**副作用**: 记录 OperationLog(action=refund)

#### 请求

```http
POST /api/v1/admin/orders/X20250613100000001/refund
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "amount": 49.00,
  "reason": "用户申请退款,使用未超过 30%"
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "order_no": "X20250613100000001",
    "refund_amount": 49.00,
    "status": "refunded",
    "refunded_at": "2025-06-13T11:00:00Z"
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | 金额超过订单金额 |
| 40401 | 订单不存在 |
| 40901 | 订单状态非 paid,不可退款 |
| 50001 | 虎皮椒退款接口失败 |

---

## 9. 兑换码管理(4 个)

### 9.1 POST /admin/codes/generate(批量生成)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
POST /api/v1/admin/codes/generate
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "type": "monthly",       // single/monthly/purchase
  "count": 100,
  "valid_days": 30,
  "batch_id": "B20250613001"  // 批次号,自定义
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "batch_id": "B20250613001",
    "count": 100,
    "codes": [
      "ABCD-EFGH-JKLM",
      "MNOP-QRST-UVWX",
      "..."
    ],
    "code_mask_samples": [
      "AB******LM",
      "MN******WX"
    ]
  }
}
```

> ⚠️ `codes` 字段仅在生成时返回 1 次,务必保存。数据库仅存 SHA256 hash + code_mask。

---

### 9.2 GET /admin/codes(兑换码列表)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/codes?batch_id=B20250613001&status=used&page=1&page_size=50
Authorization: Bearer <admin_token>
```

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| batch_id | string | 批次号过滤 |
| status | string | unused/used/revoked |
| type | string | single/monthly/purchase |
| page | int | 页码 |
| page_size | int | 默认 50,最大 200 |

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 88,
        "code_mask": "AB******LM",
        "type": "monthly",
        "points": 1200,
        "status": "used",
        "batch_id": "B20250613001",
        "user_id": 42,
        "used_at": "2025-06-13T12:00:00Z",
        "created_at": "2025-06-13T10:00:00Z"
      }
    ],
    "total": 100
  }
}
```

---

### 9.3 POST /admin/codes/{code_id}/revoke(作废)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
POST /api/v1/admin/codes/88/revoke
Authorization: Bearer <admin_token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "code_id": 88,
    "status": "revoked"
  }
}
```

---

### 9.4 GET /admin/codes/export(导出 CSV)

**鉴权**: 需要 JWT + is_admin

> V1 简化:CSV 只导出 code_mask + 状态(无明文)。如需明文请用生成时返回的 codes 字段。

#### 请求

```http
GET /api/v1/admin/codes/export?batch_id=B20250613001
Authorization: Bearer <admin_token>
```

#### 响应

```
Content-Type: text/csv
Content-Disposition: attachment; filename=redeem_B20250613001.csv

code_mask,type,points,status,user_id,used_at,created_at
AB******LM,monthly,1200,used,42,2025-06-13T12:00:00Z,2025-06-13T10:00:00Z
...
```

---

## 10. 用户管理(4 个)

### 10.1 GET /admin/users(用户列表)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/users?keyword=138&page=1&page_size=20
Authorization: Bearer <admin_token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 42,
        "phone": "138****0000",
        "nickname": "小Z",
        "invite_code": "TEST0001",
        "status": "active",  // active/disabled
        "is_admin": false,
        "created_at": "2025-06-01T10:00:00Z",
        "last_active_at": "2025-06-13T11:00:00Z"
      }
    ],
    "total": 1250
  }
}
```

---

### 10.2 GET /admin/users/{user_id}(用户详情)

**鉴权**: 需要 JWT + is_admin

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user": {
      "id": 42,
      "phone": "13800000000",
      "nickname": "小Z",
      "avatar_url": "https://oss.example.com/avatar/42.jpg",
      "invite_code": "TEST0001",
      "invite_user_id": 7,
      "status": "active",
      "is_admin": false,
      "created_at": "2025-06-01T10:00:00Z",
      "last_active_at": "2025-06-13T11:00:00Z"
    },
    "points": {
      "trial_balance": 50,
      "subscription_balance": 1200,
      "purchase_balance": 100,
      "total_balance": 1350
    },
    "stats": {
      "total_orders": 5,
      "total_spent": 245.00,
      "total_rewrites": 28,
      "referral_count": 3
    }
  }
}
```

---

### 10.3 POST /admin/users/{user_id}/disable(禁用)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
POST /api/v1/admin/users/42/disable
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "违规使用,刷改写"
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user_id": 42,
    "status": "disabled",
    "reason": "违规使用,刷改写"
  }
}
```

#### 副作用
- 记录 OperationLog
- 用户无法登录(Token 立即失效)
- 现有积分冻结(V2 才会被回收)

---

### 10.4 POST /admin/users/{user_id}/enable(启用)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
POST /api/v1/admin/users/42/enable
Authorization: Bearer <admin_token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user_id": 42,
    "status": "active"
  }
}
```

---

### 10.5 POST /admin/users/{user_id}/adjust-points(调整积分)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
POST /api/v1/admin/users/42/adjust-points
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "change": 200,
  "point_type": "purchase",
  "reason": "补偿:用户反馈改写效果差,补偿积分"
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user_id": 42,
    "change": 200,
    "point_type": "purchase",
    "new_balance": 1300
  }
}
```

#### 错误

| 错误码 | 场景 |
|-------|------|
| 40001 | change = 0 |
| 40001 | point_type 非法 |
| 40401 | 用户不存在 |

#### 副作用
- 记录 OperationLog + point_transactions
- 增加:`source=adjust`
- 减少:消耗即将过期的批次(FIFO)

---

## 11. 积分流水(2 个)

### 11.1 GET /admin/points/transactions(积分流水)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/points/transactions?user_id=42&change_type=spend&page=1&page_size=20
Authorization: Bearer <admin_token>
```

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | int | 用户 ID |
| phone | string | 手机号(与 user_id 二选一) |
| feature | string | partial_rewrite/full_rewrite |
| source | string | order/rewrite/redeem/trial/invite/adjust/refund |
| change_type | string | earn(获得)/spend(消耗) |
| start_date | string | YYYY-MM-DD |
| end_date | string | YYYY-MM-DD |
| page | int | 默认 1 |
| page_size | int | 默认 20,最大 200 |

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1024,
        "user_id": 42,
        "user_phone": "138****0000",
        "point_type": "subscription",
        "change": -50,
        "balance_before": 1300,
        "balance_after": 1250,
        "source": "rewrite",
        "feature": "partial_rewrite",
        "related_id": 88,
        "remark": "工作经历片段改写",
        "created_at": "2025-06-13T11:00:00Z"
      }
    ],
    "total": 256,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 11.2 GET /admin/points/stats(流水统计)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/points/stats?days=7
Authorization: Bearer <admin_token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "days": 7,
    "total_earned": 125000,
    "total_spent": 98500,
    "transaction_count": 1024,
    "daily": [
      {"date": "2025-06-07", "earned": 18000, "spent": 14000, "earn_count": 50, "spend_count": 90},
      {"date": "2025-06-08", "earned": 20000, "spent": 15000, "earn_count": 55, "spend_count": 95}
    ],
    "by_source": {
      "order": {"earned": 80000, "spent": 0},
      "rewrite": {"earned": 0, "spent": 70000},
      "redeem": {"earned": 25000, "spent": 0},
      "adjust": {"earned": 5000, "spent": 0}
    },
    "by_point_type": {
      "trial": {"earned": 5000, "spent": 3000, "balance": 2000},
      "subscription": {"earned": 100000, "spent": 80000, "balance": 20000},
      "purchase": {"earned": 20000, "spent": 15500, "balance": 4500}
    }
  }
}
```

---

### 11.3 POST /admin/points/adjust(管理员调账)

**鉴权**: 需要 JWT + is_admin

> 管理员手动调整用户积分(补偿、修复等场景)。

#### 请求

```http
POST /api/v1/admin/points/adjust
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": 42,
  "delta": 200,
  "remark": "补偿:用户反馈改写效果差"
}
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user_id": 42,
    "delta": 200,
    "remark": "补偿:用户反馈改写效果差"
  }
}
```

---

## 12. 操作日志(2 个)

### 12.1 GET /admin/logs(操作日志)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/logs?action=refund&page=1&page_size=20
Authorization: Bearer <admin_token>
```

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| admin_id | int | 管理员 ID |
| action | string | refund/disable_user/adjust_points/generate_codes/revoke_code |
| target_type | string | order/user/code |
| target_id | int | 目标 ID |
| start_date | string | YYYY-MM-DD |
| end_date | string | YYYY-MM-DD |
| page | int | 默认 1 |
| page_size | int | 默认 20,最大 200 |

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 512,
        "admin_id": 1,
        "admin_phone": "138****0000",
        "action": "refund",
        "target_type": "order",
        "target_id": 8888,
        "before_value": "{\"status\":\"paid\",\"amount\":49.00}",
        "after_value": "{\"status\":\"refunded\",\"refund_amount\":49.00}",
        "remark": "用户申请退款,使用未超过 30%",
        "ip": "1.2.3.4",
        "created_at": "2025-06-13T11:00:00Z"
      }
    ],
    "total": 89
  }
}
```

---

### 12.2 GET /admin/logs/stats(日志统计)

**鉴权**: 需要 JWT + is_admin

#### 请求

```http
GET /api/v1/admin/logs/stats?days=30
Authorization: Bearer <admin_token>
```

#### 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "days": 30,
    "total_actions": 156,
    "by_action": {
      "refund": 12,
      "disable_user": 3,
      "adjust_points": 25,
      "generate_codes": 8,
      "revoke_code": 1
    },
    "by_admin": {
      "1": {"count": 89, "actions": {"refund": 8, "adjust_points": 20}},
      "2": {"count": 67, "actions": {"refund": 4, "generate_codes": 8}}
    }
  }
}
```

---

## 附录 A: 鉴权 Header

所有需要鉴权的 API 都需要携带:

```http
Authorization: Bearer <jwt_token>
```

JWT 在 `/auth/login` 接口返回,有效期 30 分钟。前端应在 `localStorage.setItem('token', token)` 中存储。

---

## 附录 B: CORS 白名单

| Origin | 用途 |
|--------|------|
| `https://xiaoz-jl.com` | 生产用户端 |
| `https://www.xiaoz-jl.com` | 生产用户端(www) |
| `https://admin.xiaoz-jl.com` | 生产后台 |
| `http://localhost:5173` | 本地用户端 dev |
| `http://localhost:5174` | 本地后台 dev |

---

## 附录 C: 限流配置

| 端点 | 试用 | 付费 | VIP |
|------|------|------|-----|
| `/auth/send-sms` | 10次/天/手机 | - | - |
| `/rewrite/partial` | 10次/小时 | 50次/小时 | 200次/小时 |
| `/rewrite/full` | 3次/小时 | 15次/小时 | 60次/小时 |
| `/files/upload` | 5次/天 | 50次/天 | 200次/天 |
| 通用 | 60次/分钟 | 300次/分钟 | 1000次/分钟 |

---

## 附录 D: SDK 示例

### JavaScript / TypeScript

```typescript
// 用户端 API 客户端
import axios from 'axios'

const http = axios.create({
  baseURL: 'https://xiaoz-jl.com/api/v1',
  timeout: 60000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 登录
const { data } = await http.post('/auth/login', {
  phone: '13800000000',
  code: '123456',
})
localStorage.setItem('token', data.data.token)

// 部分改写
const { data: rewrite } = await http.post('/rewrite/partial', {
  text: '负责...',
  title: '工作经历',
})
console.log(rewrite.data.output_text)
```

### Python

```python
import requests

BASE = 'https://xiaoz-jl.com/api/v1'

# 登录
r = requests.post(f'{BASE}/auth/login', json={
    'phone': '13800000000',
    'code': '123456',
})
token = r.json()['data']['token']

# 部分改写
r = requests.post(
    f'{BASE}/rewrite/partial',
    json={'text': '负责...', 'title': '工作经历'},
    headers={'Authorization': f'Bearer {token}'},
)
print(r.json()['data']['output_text'])
```

### cURL

```bash
# 登录
TOKEN=$(curl -s -X POST https://xiaoz-jl.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800000000","code":"123456"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['token'])")

# 部分改写
curl -X POST https://xiaoz-jl.com/api/v1/rewrite/partial \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"负责...","title":"工作经历"}'
```

---

## 附录 E: 状态码对应表

| 业务码 | 含义 | 触发条件 |
|-------|------|---------|
| 0 | 成功 | - |
| 40001 | 参数错误 | 缺少必填 / 类型错误 |
| 40101 | 未登录 | 缺 Authorization 头 |
| 40102 | Token 过期 | JWT exp 已过 |
| 40103 | Token 无效 | 签名错误 / 格式错误 |
| 40301 | 无权限 | 非管理员访问 / 非本人资源 |
| 40401 | 资源不存在 | ID 错误 / 已删除 |
| 40901 | 状态冲突 | 重复创建 / 状态不符 |
| 41001 | 积分不足 | 改写前余额 < 所需积分 |
| 42901 | 限流 | 触发限流规则 |
| 50001 | 支付错误 | 虎皮椒接口失败 |
| 50002 | 短信错误 | 阿里云短信失败 |
| 50003 | LLM 错误 | DeepSeek API 失败 |
| 50004 | OSS 错误 | 阿里云 OSS 失败 |
| 50000 | 服务器异常 | 兜底错误 |

---

## 附录 F: 版本与变更

### v1.0 (2025-06-13)
- 首次发布 30 个 API
- 用户端 13 + 后台 17

### v1.1 (计划 2025-07)
- 增加 `POST /auth/logout`(Token 黑名单)
- 增加 `GET /orders`(用户查自己订单)
- 增加 `GET /points/transactions`(用户查自己积分流水)

### v2.0 (计划 2025-Q4)
- WebSocket 改写进度推送
- 团队版 / 企业版 API
- OpenAPI 3.0 spec 导出
