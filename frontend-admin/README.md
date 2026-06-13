# 小Z简历 - 前台后台 (Vue 3 + Element Plus)

## 启动

```bash
npm install
npm run dev
# 访问 http://localhost:5174
```

## 4 个核心页面

| 路径 | 页面 | 功能 |
|---|---|---|
| /login | 登录页 | 手机号+验证码(需 is_admin=true 的用户) |
| /dashboard | 数据看板 | DAU/订单/收入/AI 成本 4 个核心指标 |
| /orders | 订单管理 | 列表+筛选+退款 |
| /codes | 兑换码管理 | 批量生成+列表+作废+导出 CSV |
| /users | 用户管理 | 列表+详情+禁用+调整积分 |

## 首次登录设置

1. 后端先启动
2. 用后端脚本把手机号设为管理员:
   ```bash
   cd backend && python -m scripts.create_admin 13800000000
   ```
3. 后台登录页输入该手机号 + 验证码 123456(开发模式)

## 部署

```bash
npm run build
# 产物在 dist/
# 用 nginx 指到 dist 即可
```

## 注意事项

- 后台和用户端是两个独立项目,不会互相干扰
- 后台路由懒加载在 Layout.vue 里
- Element Plus 用 auto-import 减少样板代码
