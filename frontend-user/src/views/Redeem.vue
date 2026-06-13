<template>
  <div class="page">
    <div class="card">
      <div class="section-title">兑换码激活</div>
      <div class="text-secondary mt-8" style="font-size: 13px">
        兑换码可在闲鱼 / 程序员客栈 / 朋友圈推广处获得
      </div>

      <van-field
        v-model="code"
        class="mt-16"
        placeholder="请输入 14 位兑换码(形如 XXXX-XXXX-XXXX)"
        maxlength="14"
        clearable
      />

      <van-button
        block
        round
        type="primary"
        class="mt-16"
        :loading="loading"
        :disabled="!canSubmit"
        @click="submit"
      >
        立即兑换
      </van-button>
    </div>

    <div class="card">
      <div class="section-title">兑换码使用说明</div>
      <ul class="rules">
        <li>每张兑换码仅可使用 1 次</li>
        <li>次卡/月卡兑换码激活后积分有效期 30 天</li>
        <li>增购类兑换码激活后积分永久有效</li>
        <li>兑换码激活后不可退</li>
      </ul>
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
import { ref, computed } from 'vue'
import { showDialog, showToast } from 'vant'
import { redeemApi } from '../api/shop'
import { useUserStore } from '../stores/user'

const tabActive = ref(2)
const userStore = useUserStore()
const code = ref('')
const loading = ref(false)

const canSubmit = computed(() => code.value.length >= 8)

async function submit() {
  loading.value = true
  try {
    const data: any = await redeemApi.activate(code.value.trim().toUpperCase())
    await showDialog({
      title: '兑换成功',
      message: `获得 ${data.points} 积分(${data.type === 'single' ? '次卡' : data.type === 'monthly' ? '月卡' : '增购'}),有效期 ${data.valid_days} 天`,
      confirmButtonText: '好的',
    })
    code.value = ''
    await userStore.fetchMe()
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.section-title { font-size: 15px; font-weight: 600; }
.rules {
  margin: 12px 0 0;
  padding-left: 20px;
  font-size: 13px;
  color: #646566;
  line-height: 1.8;
}
</style>
