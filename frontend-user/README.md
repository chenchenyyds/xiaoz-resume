# 小Z简历 - 前端用户端 (Vue 3 + Vant)

## 启动

```bash
npm install
npm run dev
# 访问 http://localhost:5173
```

## 5 个核心页面

| 路径 | 页面 | 功能 |
|---|---|---|
| /login | 登录页 | 手机号+验证码 |
| /workbench | 工作台 | 积分余额、3 个改写入口、最近简历、推广码 |
| /files | 简历管理 | 上传 docx、列表、删除 |
| /redeem | 兑换码 | 激活兑换码 |
| /me | 个人中心 | 积分明细、推广码、设置 |

## 3 个核心组件

| 组件 | 用途 |
|---|---|
| `components/PartialRewrite.vue` | 部分改写弹窗(50 积分) |
| `components/FullRewrite.vue` | 完整改写弹窗(1000/1500 积分) |
| `components/ShopPanel.vue` | 充值弹窗(选套餐) |

## API 对接

通过 `vite.config.ts` 里的代理:`/api -> http://localhost:8000`
后端必须先启动,否则所有 API 调用会 404。

## 与后端的认证约定

- 用户登录后 token 存 `localStorage.token`
- 后台登录后 token 存 `localStorage.admin_token`(互不干扰)
- 每次请求通过 axios 拦截器自动加 `Authorization: Bearer xxx`
- 后端 401 状态自动跳登录页

## 注意事项

- 上传文件大小限制 10MB(由后端 `file.max_size_mb` 控制)
- 改写接口 timeout 60 秒(完整改写可能要 30-60s)
- 开发模式下验证码固定 123456,真发短信需改 SMS_DEV_MODE=false
