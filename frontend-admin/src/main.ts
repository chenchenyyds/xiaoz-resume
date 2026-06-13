import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'

import Login from './views/Login.vue'
import Layout from './views/Layout.vue'
import Dashboard from './views/Dashboard.vue'
import Orders from './views/Orders.vue'
import Codes from './views/Codes.vue'
import Users from './views/Users.vue'
import Points from './views/Points.vue'
import Logs from './views/Logs.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: Login, meta: { title: '登录' } },
    {
      path: '/',
      component: Layout,
      meta: { auth: true },
      children: [
        { path: 'dashboard', component: Dashboard, meta: { title: '数据看板' } },
        { path: 'orders', component: Orders, meta: { title: '订单管理' } },
        { path: 'codes', component: Codes, meta: { title: '兑换码管理' } },
        { path: 'users', component: Users, meta: { title: '用户管理' } },
        { path: 'points', component: Points, meta: { title: '积分流水' } },
        { path: 'logs', component: Logs, meta: { title: '操作日志' } },
      ]
    },
  ]
})

router.beforeEach((to, _, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.meta.auth && !token) next('/login')
  else next()
  if (to.meta.title) document.title = `${to.meta.title} - 小Z简历后台`
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
