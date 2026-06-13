<template>
  <div>
    <h2>数据看板</h2>
    <el-row :gutter="16" v-loading="loading">
      <el-col :span="6"><el-card><div class="metric-label">今日 DAU</div><div class="metric-val">{{ data.today_dau }}</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="metric-label">今日订单数</div><div class="metric-val text-primary">{{ data.today_orders }}</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="metric-label">今日收入 (元)</div><div class="metric-val text-success">¥{{ Number(data.today_revenue).toFixed(2) }}</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="metric-label">今日 AI 成本 (元)</div><div class="metric-val text-warning">¥{{ Number(data.today_llm_cost).toFixed(4) }}</div></el-card></el-col>
    </el-row>

    <el-row :gutter="16" class="mt-16">
      <el-col :span="8"><el-card><div class="metric-label">累计用户</div><div class="metric-val">{{ data.total_users }}</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="metric-label">累计订单</div><div class="metric-val">{{ data.total_orders }}</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="metric-label">累计收入 (元)</div><div class="metric-val text-success">¥{{ Number(data.total_revenue).toFixed(2) }}</div></el-card></el-col>
    </el-row>

    <el-alert class="mt-16" type="info" :closable="false">
      <p><strong>V1 阶段成功标准</strong>:累计 100 单 / 退款率 &lt; 15% / 至少 1 个自发转发</p>
      <p><strong>V1 失败信号</strong>:30 天 &lt; 30 单 / 退款率 &gt; 30% / 没有自发传播</p>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dashboardApi } from '../api'

const loading = ref(false)
const data = ref<any>({
  today_dau: 0, today_orders: 0, today_revenue: 0, today_llm_cost: 0,
  total_users: 0, total_orders: 0, total_revenue: 0,
})

async function load() {
  loading.value = true
  try {
    data.value = await dashboardApi.overview()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.metric-label { color: #909399; font-size: 13px; }
.metric-val { font-size: 28px; font-weight: bold; margin-top: 8px; }
.text-primary { color: #1989fa; }
.text-success { color: #67c23a; }
.text-warning { color: #e6a23c; }
.mt-16 { margin-top: 16px; }
h2 { margin: 0 0 16px; }
</style>
