<template>
  <div class="logs-page">
    <h2 style="margin: 0 0 16px">📋 操作日志</h2>

    <!-- 统计 -->
    <el-card style="margin-bottom: 16px" v-if="Object.keys(stats.by_action || {}).length">
      <template #header>操作类型分布(最近 {{ stats.days }} 天)</template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="(count, action) in stats.by_action" :key="action">
          <div class="action-stat">
            <div class="action-name">{{ actionLabels[action as string] || action }}</div>
            <div class="action-count">{{ count }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 筛选 -->
    <el-card style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="管理员ID">
          <el-input v-model.number="filters.admin_id" placeholder="管理员ID" clearable style="width: 140px" />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="filters.action" placeholder="全部" clearable style="width: 180px">
            <el-option label="订单退款" value="refund" />
            <el-option label="禁用用户" value="disable_user" />
            <el-option label="启用用户" value="enable_user" />
            <el-option label="调整积分" value="adjust_points" />
            <el-option label="生成兑换码" value="generate_codes" />
            <el-option label="作废兑换码" value="revoke_code" />
            <el-option label="更新配置" value="update_config" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标">
          <el-select v-model="filters.target_type" placeholder="全部" clearable style="width: 120px">
            <el-option label="订单" value="order" />
            <el-option label="用户" value="user" />
            <el-option label="兑换码" value="code" />
            <el-option label="配置" value="config" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="success" @click="exportCSV">导出 CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="admin_phone" label="操作人" width="140" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-tag size="small" :type="actionColor(row.action)">
              {{ actionLabels[row.action] || row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="目标" width="100" />
        <el-table-column prop="target_id" label="目标ID" width="100" />
        <el-table-column label="变更前" show-overflow-tooltip>
          <template #default="{ row }">
            <code v-if="row.before_value" style="font-size: 11px">{{ JSON.stringify(row.before_value) }}</code>
            <span v-else style="color: #C0C4CC">-</span>
          </template>
        </el-table-column>
        <el-table-column label="变更后" show-overflow-tooltip>
          <template #default="{ row }">
            <code v-if="row.after_value" style="font-size: 11px">{{ JSON.stringify(row.after_value) }}</code>
            <span v-else style="color: #C0C4CC">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="created_at" label="时间" width="170" />
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadData"
        @size-change="loadData"
        style="margin-top: 16px; justify-content: flex-end; display: flex"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const stats = ref<any>({ days: 7, by_action: {}, by_admin: {} })

const filters = reactive<any>({
  admin_id: null,
  action: '',
  target_type: '',
  dateRange: [],
})

const actionLabels: Record<string, string> = {
  refund: '订单退款',
  disable_user: '禁用用户',
  enable_user: '启用用户',
  adjust_points: '调整积分',
  generate_codes: '生成兑换码',
  revoke_code: '作废兑换码',
  update_config: '更新配置',
  login: '后台登录',
}

function actionColor(action: string) {
  const map: Record<string, string> = {
    refund: 'danger',
    disable_user: 'danger',
    adjust_points: 'warning',
    generate_codes: 'success',
    revoke_code: 'info',
    update_config: 'warning',
  }
  return (map[action] || 'info') as any
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.admin_id) params.admin_id = filters.admin_id
    if (filters.action) params.action = filters.action
    if (filters.target_type) params.target_type = filters.target_type
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    const resp: any = await http.get('/admin/logs', { params })
    if (resp.code === 0) {
      items.value = resp.data.items
      total.value = resp.data.total
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const resp: any = await http.get('/admin/logs/stats', { params: { days: 7 } })
    if (resp.code === 0) stats.value = resp.data
  } catch (e) {
    console.error('stats 加载失败', e)
  }
}

function resetFilters() {
  filters.admin_id = null
  filters.action = ''
  filters.target_type = ''
  filters.dateRange = []
  page.value = 1
  loadData()
}

function exportCSV() {
  const headers = ['ID', '操作人', '操作', '目标类型', '目标ID', '变更前', '变更后', '备注', 'IP', '时间']
  const rows = items.value.map((i: any) => [
    i.id, i.admin_phone, actionLabels[i.action] || i.action,
    i.target_type || '', i.target_id || '',
    i.before_value ? JSON.stringify(i.before_value) : '',
    i.after_value ? JSON.stringify(i.after_value) : '',
    i.remark || '', i.ip || '', i.created_at,
  ])
  const csv = [headers, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `操作日志_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出')
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.action-stat { text-align: center; padding: 8px; }
.action-name { color: #909399; font-size: 13px; }
.action-count { font-size: 24px; font-weight: 700; color: #1E88E5; margin-top: 4px; }
code { background: #f5f7fa; padding: 2px 4px; border-radius: 3px; }
</style>
