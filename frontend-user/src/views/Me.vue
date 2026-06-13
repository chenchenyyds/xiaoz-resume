<template>
  <div class="page">
    <div class="card profile-card">
      <div class="flex" style="gap: 12px; align-items: center">
        <van-image
          round
          width="56"
          height="56"
          :src="userStore.user?.avatar_url || defaultAvatar"
        />
        <div>
          <div style="font-size: 16px; font-weight: 600">{{ userStore.user?.nickname || '匿名用户' }}</div>
          <div class="text-secondary" style="font-size: 12px">{{ maskedPhone }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">积分余额</div>
      <div class="points-grid">
        <div class="points-block">
          <div class="points-val text-primary">{{ userStore.points.subscription_balance }}</div>
          <div class="points-label">订阅积分</div>
        </div>
        <div class="points-block">
          <div class="points-val">{{ userStore.points.trial_balance }}</div>
          <div class="points-label">试用积分</div>
        </div>
        <div class="points-block">
          <div class="points-val">{{ userStore.points.purchase_balance }}</div>
          <div class="points-label">增购积分</div>
        </div>
      </div>
      <div class="text-secondary mt-12" style="font-size: 12px">
        订阅积分会过期,先消耗;增购积分永久有效
      </div>
    </div>

    <div class="card">
      <div class="section-title">我的推广</div>
      <div class="text-secondary" style="font-size: 13px">推广码</div>
      <div class="text-primary mt-8" style="font-size: 20px; font-weight: bold; letter-spacing: 1px">
        {{ userStore.user?.invite_code }}
      </div>
      <div class="text-secondary mt-8" style="font-size: 12px">
        好友通过你的推广码注册,你和他各得 200 积分
      </div>
      <van-button class="mt-12" block size="small" @click="copyInvite">复制推广码</van-button>
    </div>

    <div class="card">
      <van-cell title="联系客服" is-link @click="contact" />
      <van-cell title="用户协议" is-link @click="goAgreement" />
      <van-cell title="退出登录" is-link center @click="confirmLogout" />
    </div>

    <van-tabbar v-model="tabActive" route>
      <van-tabbar-item to="/workbench" icon="home-o">工作台</van-tabbar-item>
      <van-tabbar-item to="/files" icon="orders-o">简历</van-tabbar-item>
      <van-tabbar-item to="/redeem" icon="coupon-o">兑换</van-tabbar-item>
      <van-tabbar-item to="/me" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const tabActive = ref(3)

const defaultAvatar = 'data:image/svg+xml;base64,...'  // 简化

const maskedPhone = computed(() => {
  const p = userStore.user?.phone || ''
  if (p.length === 11) return `${p.slice(0, 3)}****${p.slice(7)}`
  return p
})

async function copyInvite() {
  const code = userStore.user?.invite_code || ''
  if (code) {
    try {
      await navigator.clipboard.writeText(code)
      showToast('已复制')
    } catch { showToast('复制失败') }
  }
}

function contact() {
  // V1:暂时复制微信号让用户加
  showDialog({ title: '联系客服', message: '微信:小Z简历助手\n工作时间:工作日 10-18 点' })
}

function goAgreement() {
  showDialog({ title: '用户协议', message: 'V1 阶段简版协议,后续补充' })
}

function confirmLogout() {
  showDialog({ title: '退出登录?', message: '退出后需要重新验证手机号' }).then(() => {
    userStore.logout()
  }).catch(() => {})
}

onMounted(async () => {
  if (!userStore.user) await userStore.fetchMe()
})
</script>

<style scoped>
.profile-card { background: linear-gradient(135deg, #fff 0%, #f7f8fa 100%); }

.section-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }

.points-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.points-block {
  text-align: center;
  background: #f7f8fa;
  padding: 12px;
  border-radius: 6px;
}
.points-val {
  font-size: 22px;
  font-weight: bold;
}
.points-label {
  font-size: 11px;
  color: #969799;
  margin-top: 2px;
}
</style>
