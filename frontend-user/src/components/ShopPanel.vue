<template>
  <div class="shop-panel">
    <div class="panel-header">
      <div class="title">选择套餐</div>
      <van-icon name="cross" size="20" @click="$emit('close')" />
    </div>

    <div class="panel-body">
      <van-empty v-if="loading" description="加载中..." :image-size="60" />
      <van-cell-group v-else inset>
        <van-cell
          v-for="p in products"
          :key="p.code"
          :title="p.name"
          :label="p.description"
          :value="`¥${p.price}`"
          is-link
          @click="buy(p)"
        />
      </van-cell-group>

      <div class="mt-16 text-secondary text-center" style="font-size: 12px">
        支付由虎皮椒支持,7 天内未使用可全额退款
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { productApi, orderApi } from '../api/shop'

const emit = defineEmits(['close', 'paid'])

const products = ref<any[]>([])
const loading = ref(false)

async function loadProducts() {
  loading.value = true
  try {
    const data: any = await productApi.list()
    products.value = data.items || []
  } finally {
    loading.value = false
  }
}

async function buy(p: any) {
  showLoadingToast({ message: '创建订单...', forbidClick: true })
  try {
    const order: any = await orderApi.create(p.code)
    closeToast()
    if (order.pay_url) {
      // 跳到虎皮椒支付(V1 直接 window.open)
      window.open(order.pay_url, '_blank')
      // 提示用户支付完成后回这里
      setTimeout(() => {
        showToast('支付完成请刷新页面查看积分')
        emit('paid')
      }, 500)
    } else {
      showToast('获取支付链接失败')
    }
  } catch (e) {
    closeToast()
  }
}

onMounted(loadProducts)
</script>

<style scoped>
.shop-panel {
  background: white;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebedf0;
}
.title { font-size: 16px; font-weight: 600; }
.panel-body { flex: 1; overflow-y: auto; padding: 16px 0; }
.text-center { text-align: center; }
</style>
