<template>
  <el-container class="layout">
    <el-aside width="200px" class="sidebar">
      <div class="logo">小Z简历</div>
      <el-menu :default-active="active" router :collapse="false">
        <el-menu-item index="/dashboard"><el-icon><DataLine /></el-icon>数据看板</el-menu-item>
        <el-menu-item index="/orders"><el-icon><Tickets /></el-icon>订单管理</el-menu-item>
        <el-menu-item index="/codes"><el-icon><Postcard /></el-icon>兑换码管理</el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
        <el-menu-item index="/points"><el-icon><Money /></el-icon>积分流水</el-menu-item>
        <el-menu-item index="/logs"><el-icon><Document /></el-icon>操作日志</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>{{ currentTitle }}</span>
        <el-button text @click="logout">退出</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { DataLine, Tickets, Postcard, User, Money, Document } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const active = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '后台')

function logout() {
  ElMessageBox.confirm('确定退出?', '提示').then(() => {
    localStorage.removeItem('admin_token')
    router.replace('/login')
  }).catch(() => {})
}
</script>

<style scoped>
.layout { min-height: 100vh; }
.sidebar { background: #001529; color: white; }
.sidebar .logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
}
.sidebar :deep(.el-menu) { background: transparent; border: none; }
.sidebar :deep(.el-menu-item) { color: rgba(255,255,255,0.85); }
.sidebar :deep(.el-menu-item.is-active) { background: #1989fa; }
.sidebar :deep(.el-menu-item:hover) { background: #1f2d3d; }
.header {
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #f0f0f0;
}
.el-main { background: #f0f2f5; }
</style>
