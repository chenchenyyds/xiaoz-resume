<template>
  <div class="points-page">
    <h2 style="margin: 0 0 16px">💰 积分流水</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card>
          <div class="metric">
            <div class="metric-label">总发放</div>
            <div class="metric-value" style="color: #67C23A">+{{ stats.total_earned || 0 }}</div>
            <div class="metric-sub">最近 {{ stats.days }} 天</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="metric">
            <div class="metric-label">总消耗</div>
            <div class="metric-value" style="color: #F56C6C">-{{ stats.total_spent || 0 }}</div>
            <div class="metric-sub">最近 {{ stats.days }} 天</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="metric">
            <div class="metric-label">交易笔数</div>
            <div class="metric-value">{{ stats.transaction_count || 0 }}</div>
            <div class="metric-sub">日均 {{ Math.round((stats.transaction_count || 0) / (stats.days || 1)) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="metric">
            <div class="metric-label">净变化</div>
            <div class="metric-value" :style="{color: (stats.total_earned - stats.total_spent) >= 0 ? '#67C23A' : '#F56C6C'}">
              {{ (stats.total_earned || 0) - (stats.total_spent || 0) > 0 ? '+' : '' }}{{ (stats.total_earned || 0) - (stats.total_spent || 0) }}
            </div>
            <div class="metric-sub">发放 - 消耗</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势图(用 el-table 简单展示) -->
    <el-card style="margin-bottom: 16px" v-if="stats.daily && stats.daily.length">
      <template #header>每日趋势</template>
      <el-table :data="stats.daily" size="small" max-height="200">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column label="发放">
          <template #default="{ row }">
            <span style="color: #67C23A">+{{ row.earned }}</span>
          </template>
        </el-table-column>
        <el-table-column label="消耗">
          <template #default="{ row }">
            <span style="color: #F56C6C">-{{ row.spent }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="earn_count" label="发放笔数" width="100" />
        <el-table-column prop="spend_count" label="消耗笔数" width="100" />
      </el-table>
    </el-card>

    <!-- 筛选 -->
    <el-card style="margin-bottom: 16px">
      <el-form :inline="true">
        <el-form-item label="手机号">
          <el-input v-model="filters.phone" placeholder="按手机号筛选" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input v-model.number="filters.user_id" placeholder="用户ID" clearable style="width: 120px" />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="filters.source" placeholder="全部" clearable style="width: 140px">
            <el-option label="订单" value="order" />
            <el-option label="改写消耗" value="rewrite" />
            <el-option label="兑换码" value="redeem" />
            <el-option label="试用" value="trial" />
            <el-option label="推广邀请" value="invite" />
            <el-option label="管理员调整" value="adjust" />
            <el-option label="退款" value="refund" />
          </el-select>
        </el-form-item>
        <el-form-item label="变动">
          <el-select v-model="filters.change_type" placeholder="全部" clearable style="width: 120px">
            <el-option label="获得" value="earn" />
            <el-option label="消耗" value="spend" />
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

    <!-- 流水列表 -->
    <el-card>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="user_phone" label="用户" width="140" />
        <el-table-column prop="point_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.point_type === 'purchase' ? 'success' : row.point_type === 'subscription' ? 'warning' : 'info'">
              {{ row.point_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变动" width="100">
          <template #default="{ row }">
            <span :style="{color: row.change > 0 ? '#67C23A' : '#F56C6C', fontWeight: 600}">
              {{ row.change > 0 ? '+' : '' }}{{ row.change }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="余额" width="120">
          <template #default="{ row }">
            <span style="color: #909399">{{ row.balance_before }} → {{ row.balance_after }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column prop="feature" label="功能" width="140" />
        <el-table-column prop="related_id" label="关联ID" width="100" />
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
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
import { ref, onMounted, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const stats = ref<any>({ days: 7, total_earned: 0, total_spent: 0, transaction_count: 0, daily: [] })

const filters = reactive<any>({
  phone: '',
  user_id: null,
  source: '',
  change_type: '',
  dateRange: [],
})

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.phone) params.phone = filters.phone
    if (filters.user_id) params.user_id = filters.user_id
    if (filters.source) params.source = filters.source
    if (filters.change_type) params.change_type = filters.change_type
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    const resp: any = await http.get('/admin/points/transactions', { params })
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
    const resp: any = await http.get('/admin/points/stats', { params: { days: 7 } })
    if (resp.code === 0) stats.value = resp.data
  } catch (e) {
    console.error('stats 加载失败', e)
  }
}

function resetFilters() {
  filters.phone = ''
  filters.user_id = null
  filters.source = ''
  filters.change_type = ''
  filters.dateRange = []
  page.value = 1
  loadData()
}

function exportCSV() {
  // 简单 CSV 导出
  const headers = ['ID', '用户', '类型', '变动', '变动前', '变动后', '来源', '功能', '关联ID', '备注', '时间']
  const rows = items.value.map((i: any) => [
    i.id, i.user_phone, i.point_type, i.change,
    i.balance_before, i.balance_after, i.source, i.feature || '',
    i.related_id || '', i.remark || '', i.created_at,
  ])
  const csv = [headers, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `积分流水_${new Date().toISOString().slice(0, 10)}.csv`
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
.metric { text-align: center; padding: 8px 0; }
.metric-label { color: #909399; font-size: 13px; }
.metric-value { font-size: 28px; font-weight: 700; margin: 8px 0; }
.metric-sub { color: #C0C4CC; font-size: 12px; }
</style>
