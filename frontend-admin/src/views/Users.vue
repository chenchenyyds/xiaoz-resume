<template>
  <div>
    <h2>用户管理</h2>
    <el-card>
      <el-form :inline="true" :model="filter" @submit.prevent>
        <el-form-item label="手机号/昵称">
          <el-input v-model="filter.keyword" placeholder="模糊搜索" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" clearable style="width: 120px">
            <el-option label="正常" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load(1)">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="nickname" label="昵称" width="140" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_points_earned" label="累计获得积分" width="120" />
        <el-table-column prop="total_points_used" label="累计消耗积分" width="120" />
        <el-table-column prop="total_orders" label="订单数" width="80" />
        <el-table-column prop="total_spent" label="累计消费" width="100" />
        <el-table-column prop="invite_code" label="推广码" width="120" />
        <el-table-column prop="created_at" label="注册时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="last_active_at" label="最后活跃" width="170">
          <template #default="{ row }">{{ row.last_active_at ? formatTime(row.last_active_at) : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'active'" size="small" type="danger" @click="disable(row)">禁用</el-button>
            <el-button v-else size="small" type="success" @click="enable(row)">启用</el-button>
            <el-button size="small" type="warning" @click="adjustPoints(row)">调积分</el-button>
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

    <!-- 用户详情 -->
    <el-dialog v-model="detailDialog" title="用户详情" width="700px">
      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.phone }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ detail.nickname }}</el-descriptions-item>
        <el-descriptions-item label="推广码">{{ detail.invite_code }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detail.status === 'active' ? 'success' : 'danger'" size="small">
            {{ detail.status === 'active' ? '正常' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="管理员">
          <el-tag v-if="detail.is_admin" type="warning" size="small">是</el-tag>
          <span v-else>否</span>
        </el-descriptions-item>
        <el-descriptions-item label="累计获得积分">{{ detail.total_points_earned }}</el-descriptions-item>
        <el-descriptions-item label="累计消耗积分">{{ detail.total_points_used }}</el-descriptions-item>
        <el-descriptions-item label="订单数">{{ detail.total_orders }}</el-descriptions-item>
        <el-descriptions-item label="累计消费">¥{{ Number(detail.total_spent).toFixed(2) }}</el-descriptions-item>
      </el-descriptions>

      <h4 class="mt-16">最近积分流水</h4>
      <el-table :data="detail?.point_transactions || []" size="small" max-height="200">
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="point_type" label="类型" width="80" />
        <el-table-column prop="change" label="变动" width="80">
          <template #default="{ row }">
            <span :class="row.change > 0 ? 'text-success' : 'text-danger'">
              {{ row.change > 0 ? '+' : '' }}{{ row.change }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="balance_after" label="余额后" width="80" />
        <el-table-column prop="source" label="来源" width="100" />
        <el-table-column prop="remark" label="备注" />
      </el-table>
    </el-dialog>

    <!-- 调整积分 -->
    <el-dialog v-model="adjustDialog" title="调整积分" width="400px">
      <el-form :model="adjustForm" label-width="100px">
        <el-form-item label="用户">{{ adjustForm.nickname }}</el-form-item>
        <el-form-item label="变动(正负)">
          <el-input-number v-model="adjustForm.change" :min="-100000" :max="100000" />
        </el-form-item>
        <el-form-item label="账户类型">
          <el-select v-model="adjustForm.point_type" style="width: 200px">
            <el-option label="增购(永久)" value="purchase" />
            <el-option label="订阅(30天)" value="subscription" />
            <el-option label="试用(90天)" value="trial" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="adjustForm.reason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAdjust" :loading="adjusting">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminUserApi } from '../api'

const filter = ref<any>({ keyword: '', status: '', page: 1, page_size: 20 })
const users = ref<any[]>([])
const total = ref(0)
const loading = ref(false)

const detailDialog = ref(false)
const detail = ref<any>(null)

const adjustDialog = ref(false)
const adjustForm = ref<any>({ user_id: 0, nickname: '', change: 0, point_type: 'purchase', reason: '' })
const adjusting = ref(false)

function formatTime(s: string) {
  return s ? new Date(s).toLocaleString('zh-CN') : '-'
}

async function load(page?: number) {
  if (page) filter.value.page = page
  loading.value = true
  try {
    const data: any = await adminUserApi.list(filter.value)
    users.value = data.items || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function showDetail(row: any) {
  detail.value = await adminUserApi.detail(row.id)
  detailDialog.value = true
}

async function disable(row: any) {
  try {
    await ElMessageBox.confirm(`禁用用户 ${row.phone}?`, '提示', {
      inputType: 'textarea',
      inputPlaceholder: '禁用原因(选填)',
    }).then(async ({ value }: any) => {
      await adminUserApi.disable(row.id, value)
      ElMessage.success('已禁用')
      await load()
    })
  } catch (e) {}
}

async function enable(row: any) {
  await adminUserApi.enable(row.id)
  ElMessage.success('已启用')
  await load()
}

function adjustPoints(row: any) {
  adjustForm.value = { user_id: row.id, nickname: row.nickname, change: 0, point_type: 'purchase', reason: '' }
  adjustDialog.value = true
}

async function submitAdjust() {
  if (!adjustForm.value.reason) {
    ElMessage.warning('请填写原因')
    return
  }
  adjusting.value = true
  try {
    await adminUserApi.adjustPoints(
      adjustForm.value.user_id,
      adjustForm.value.change,
      adjustForm.value.point_type,
      adjustForm.value.reason,
    )
    ElMessage.success('已调整')
    adjustDialog.value = false
    await load()
  } finally {
    adjusting.value = false
  }
}

onMounted(() => load(1))
</script>

<style scoped>
.mt-16 { margin-top: 16px; }
h2 { margin: 0 0 16px; }
h4 { margin: 16px 0 8px; }
.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
</style>
