<template>
  <div class="login-page">
    <div class="login-box">
      <h2>小Z简历 - 后台管理</h2>
      <el-form :model="form" label-width="80px" @submit.prevent="onLogin">
        <el-form-item label="手机号">
          <el-input v-model="form.phone" maxlength="11" placeholder="管理员手机号" />
        </el-form-item>
        <el-form-item label="验证码">
          <el-input v-model="form.code" maxlength="6" placeholder="开发模式填 123456" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onLogin" native-type="submit">登录</el-button>
        </el-form-item>
      </el-form>
      <div class="dev-tip">开发模式验证码固定 123456,需先运行 <code>python -m scripts.create_admin 13800000000</code> 设为管理员</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api'

const router = useRouter()
const form = ref({ phone: '', code: '' })
const loading = ref(false)

async function onLogin() {
  if (!form.value.phone || !form.value.code) {
    ElMessage.warning('请填写手机号和验证码')
    return
  }
  loading.value = true
  try {
    const data: any = await authApi.login(form.value.phone, form.value.code)
    if (!data.is_admin) {
      ElMessage.error('该用户不是管理员')
      return
    }
    localStorage.setItem('admin_token', data.token)
    ElMessage.success('登录成功')
    router.replace('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.login-box {
  background: white;
  padding: 32px 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  width: 400px;
}
h2 { text-align: center; margin: 0 0 24px; }
.dev-tip { margin-top: 12px; font-size: 12px; color: #909399; text-align: center; }
code { background: #f5f7fa; padding: 1px 4px; border-radius: 3px; }
</style>
