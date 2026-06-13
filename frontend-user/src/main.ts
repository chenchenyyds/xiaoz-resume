import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import Vant from 'vant'
import 'vant/lib/index.css'
import App from './App.vue'
import './styles/main.css'

import Login from './views/Login.vue'
import Workbench from './views/Workbench.vue'
import Files from './views/Files.vue'
import Redeem from './views/Redeem.vue'
import Me from './views/Me.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/workbench' },
    { path: '/login', component: Login, meta: { title: '登录' } },
    { path: '/workbench', component: Workbench, meta: { title: '工作台', auth: true } },
    { path: '/files', component: Files, meta: { title: '我的简历', auth: true } },
    { path: '/redeem', component: Redeem, meta: { title: '兑换码', auth: true } },
    { path: '/me', component: Me, meta: { title: '我的', auth: true } },
  ]
})

// 简单路由守卫
router.beforeEach((to, _, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.auth && !token) {
    next('/login')
  } else {
    next()
  }
  if (to.meta.title) {
    document.title = `${to.meta.title} - 小Z简历`
  }
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Vant)
app.mount('#app')
