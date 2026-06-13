<template>
  <div class="page">
    <!-- 积分余额卡 -->
    <div class="card points-card">
      <div class="flex-between">
        <div>
          <div class="text-secondary" style="font-size: 12px">积分余额</div>
          <div class="points-num">{{ userStore.points.total_balance }}</div>
        </div>
        <van-button type="primary" size="small" round @click="showShop = true">
          充值
        </van-button>
      </div>
      <div class="flex mt-12 text-secondary" style="font-size: 12px; gap: 16px">
        <span>订阅 {{ userStore.points.subscription_balance }}</span>
        <span>试用 {{ userStore.points.trial_balance }}</span>
        <span>增购 {{ userStore.points.purchase_balance }}</span>
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="card">
      <div class="section-title">改写服务</div>
      <van-grid :column-num="2" :border="false" :gutter="8">
        <van-grid-item @click="showPartial = true">
          <div class="feature-icon" style="background: #e8f3ff; color: #1989fa">✍️</div>
          <div class="feature-name">部分改写</div>
          <div class="feature-desc">50 积分/次</div>
        </van-grid-item>
        <van-grid-item @click="showFull = true">
          <div class="feature-icon" style="background: #fff4e6; color: #ff976a">📄</div>
          <div class="feature-name">完整改写</div>
          <div class="feature-desc">1000 积分起</div>
        </van-grid-item>
      </van-grid>
    </div>

    <!-- 我的简历(最近 3 个) -->
    <div class="card">
      <div class="flex-between mb-12">
        <div class="section-title">我的简历</div>
        <span class="text-primary" style="font-size: 13px" @click="$router.push('/files')">查看全部 ›</span>
      </div>
      <van-empty v-if="files.length === 0" description="还没有上传简历" :image-size="60" />
      <div v-else>
        <div v-for="f in files.slice(0, 3)" :key="f.id" class="file-item">
          <van-icon name="description" size="20" color="#1989fa" />
          <span class="file-name">{{ f.file_name }}</span>
          <span class="text-placeholder" style="font-size: 12px">{{ formatTime(f.created_at) }}</span>
        </div>
      </div>
      <div class="mt-12">
        <van-button block plain type="primary" @click="$router.push('/files')">
          上传新简历
        </van-button>
      </div>
    </div>

    <!-- 推广 -->
    <div class="card">
      <div class="section-title">邀请好友,各得 200 积分</div>
      <div class="text-secondary mt-8" style="font-size: 12px">
        你的推广码:<span class="text-primary" style="font-weight: bold">{{ userStore.user?.invite_code }}</span>
      </div>
      <van-button class="mt-12" block size="small" @click="copyInvite">
        复制推广码
      </van-button>
    </div>

    <!-- 底部导航 -->
    <van-tabbar v-model="tabActive" route>
      <van-tabbar-item to="/workbench" icon="home-o">工作台</van-tabbar-item>
      <van-tabbar-item to="/files" icon="orders-o">简历</van-tabbar-item>
      <van-tabbar-item to="/redeem" icon="coupon-o">兑换</van-tabbar-item>
      <van-tabbar-item to="/me" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>

    <!-- 部分改写弹窗 -->
    <van-popup v-model:show="showPartial" position="bottom" round :style="{ height: '80%' }">
      <PartialRewrite @done="onPartialDone" />
    </van-popup>

    <!-- 完整改写弹窗 -->
    <van-popup v-model:show="showFull" position="bottom" round :style="{ height: '85%' }">
      <FullRewrite @done="onFullDone" />
    </van-popup>

    <!-- 充值弹窗 -->
    <van-popup v-model:show="showShop" position="bottom" round :style="{ height: '60%' }">
      <ShopPanel @paid="onPaid" />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '../stores/user'
import { fileApi } from '../api/files'
import PartialRewrite from '../components/PartialRewrite.vue'
import FullRewrite from '../components/FullRewrite.vue'
import ShopPanel from '../components/ShopPanel.vue'

const router = useRouter()
const userStore = useUserStore()

const tabActive = ref(0)
const showPartial = ref(false)
const showFull = ref(false)
const showShop = ref(false)
const files = ref<any[]>([])

async function loadFiles() {
  try {
    const data: any = await fileApi.list()
    files.value = data.items || []
  } catch (e) {}
}

async function copyInvite() {
  const code = userStore.user?.invite_code || ''
  if (code) {
    try {
      await navigator.clipboard.writeText(code)
      showToast('已复制')
    } catch {
      showToast('复制失败')
    }
  }
}

function formatTime(s: string) {
  const d = new Date(s)
  return `${d.getMonth() + 1}-${d.getDate()}`
}

async function onPartialDone() {
  showPartial.value = false
  await userStore.fetchMe()
  showToast('改写完成')
}

async function onFullDone() {
  showFull.value = false
  await userStore.fetchMe()
  await loadFiles()
  showToast('完整改写完成')
}

async function onPaid() {
  showShop.value = false
  await userStore.fetchMe()
  showToast('支付完成,积分已到账')
}

onMounted(async () => {
  if (!userStore.user) await userStore.fetchMe()
  await loadFiles()
})
</script>

<style scoped>
.points-card {
  background: linear-gradient(135deg, #1989fa 0%, #4fa5f5 100%);
  color: white;
}
.points-card .text-secondary { color: rgba(255,255,255,0.85) !important; }
.points-num {
  font-size: 36px;
  font-weight: bold;
  margin-top: 4px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin: 0 auto 8px;
}

.feature-name {
  font-size: 14px;
  font-weight: 500;
}

.feature-desc {
  font-size: 12px;
  color: #969799;
  margin-top: 2px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #f2f3f5;
}
.file-item:last-child { border-bottom: none; }
.file-name {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
