<template>
  <div>
    <h2>订单管理</h2>
    <el-card>
      <el-form :inline="true" :model="filter" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filter.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已退款" value="refunded" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品">
          <el-select v-model="filter.product_code" clearable placeholder="全部" style="width: 140px">
            <el-option label="次卡" value="single" />
            <el-option label="月卡" value="monthly" />
            <el-option label="增购" value="points_1000" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load(1)">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="200" />
        <el-table-column prop="user_phone" label="用户手机" width="140" />
        <el-table-column prop="product_code" label="商品" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ productName(row.product_code) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" />
        <el-table-column prop="pay_amount" label="实付" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="paid_at" label="支付时间" width="170">
          <template #default="{ row }">{{ row.paid_at ? formatTime(row.paid_at) : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'paid'" size="small" type="danger" @click="refundOrder(row)">退款</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="mt-16"
        v-model:current-page="filter.page"
        v-model:page-size="filter.page_size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="load()"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { adminOrderApi } from '../api'

const filter = ref<any>({ status: '', product_code: '', page: 1, page_size: 20 })
const orders = ref<any[]>([])
const total = ref(0)
const loading = ref(false)

function productName(code: string) {
  return { single: '次卡', monthly: '月卡', points_1000: '增购' }[code] || code
}
function statusText(s: string) {
  return { pending: '待支付', paid: '已支付', refunded: '已退款', closed: '已关闭' }[s] || s
}
function statusType(s: string) {
  return { paid: 'success', refunded: 'warning', closed: 'info' }[s] || ''
}
function formatTime(s: string) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN')
}

async function load(page?: number) {
  if (page) filter.value.page = page
  loading.value = true
  try {
    const data: any = await adminOrderApi.list(filter.value)
    orders.value = data.items || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function refundOrder(row: any) {
  try {
    const { value } = await ElMessageBox.prompt(`退款给订单 ${row.order_no},留个原因`, '退款确认', {
      inputType: 'textarea',
      inputPlaceholder: '退款原因',
      inputValidator: (v: string) => !!v || '请填写原因',
    })
    await adminOrderApi.refund(row.order_no, null, value)
    ElMessage.success('退款成功')
    await load()
  } catch (e) {}
}

onMounted(() => load(1))
</script>

<style scoped>
.mt-16 { margin-top: 16px; }
h2 { margin: 0 0 16px; }
</style>
