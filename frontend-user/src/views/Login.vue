<template>
  <div class="login-page">
    <div class="brand">
      <div class="logo">小Z简历</div>
      <div class="slogan">9.9 元 · 30 秒拿到 AI 改写简历</div>
    </div>

    <div class="card">
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="phone"
            type="tel"
            name="phone"
            label="手机号"
            placeholder="请输入手机号"
            maxlength="11"
            :rules="[{ required: true, message: '请输入手机号' }]"
          />
          <van-field
            v-model="code"
            name="code"
            label="验证码"
            placeholder="6 位验证码"
            maxlength="6"
            :rules="[{ required: true, message: '请输入验证码' }]"
          >
            <template #button>
              <van-button
                size="small"
                type="primary"
                plain
                :disabled="countdown > 0"
                @click="sendSms"
              >
                {{ countdown > 0 ? `${countdown}s 后重发` : '发送验证码' }}
              </van-button>
            </template>
          </van-field>
          <van-field
            v-model="inviteCode"
            name="inviteCode"
            label="推广码"
            placeholder="选填,填了双方都送积分"
            maxlength="16"
          />
        </van-cell-group>

        <div style="margin: 16px">
          <van-button
            round
            block
            type="primary"
            native-type="submit"
            :loading="loading"
            loading-text="登录中..."
          >
            登录 / 注册
          </van-button>
        </div>
      </van-form>

      <div class="dev-tip" v-if="devCode">
        🔧 开发模式验证码: <strong>{{ devCode }}</strong>
      </div>
    </div>

    <div class="footer">
      登录即同意《用户协议》《隐私政策》
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const phone = ref('')
const code = ref('')
const inviteCode = ref('')
const loading = ref(false)
const countdown = ref(0)
const devCode = ref<string | null>(null)

async function sendSms() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    showToast('手机号格式错误')
    return
  }
  try {
    const data: any = await userStore.sendSms(phone.value)
    if (data?.dev_code) devCode.value = data.dev_code
    showToast('验证码已发送')
    countdown.value = 60
    const t = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(t)
    }, 1000)
  } catch (e) {
    // 错误已由 http 拦截器处理
  }
}

async function onSubmit() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    showToast('手机号格式错误')
    return
  }
  loading.value = true
  try {
    await userStore.login(phone.value, code.value, inviteCode.value || undefined)
    showToast('登录成功')
    router.replace('/workbench')
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1989fa 0%, #4fa5f5 30%, #f7f8fa 30%);
  padding: 0 16px;
}

.brand {
  text-align: center;
  padding: 60px 0 40px;
  color: white;
}

.logo {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.slogan {
  font-size: 14px;
  opacity: 0.95;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 20px 0;
  margin-top: 8px;
}

.dev-tip {
  margin: 16px;
  padding: 10px;
  background: #fff7e6;
  border-radius: 6px;
  font-size: 13px;
  color: #ad6800;
  text-align: center;
}

.footer {
  text-align: center;
  color: #969799;
  font-size: 12px;
  padding: 24px 0;
}
</style>
