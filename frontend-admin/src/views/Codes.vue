<template>
  <div>
    <h2>兑换码管理</h2>

    <el-card class="mb-16">
      <el-form :inline="true" :model="genForm">
        <el-form-item label="类型">
          <el-select v-model="genForm.type" style="width: 120px">
            <el-option label="次卡" value="single" />
            <el-option label="月卡" value="monthly" />
            <el-option label="增购" value="points_1000" />
            <el-option label="试用" value="trial" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="genForm.count" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="有效期(天)">
          <el-input-number v-model="genForm.valid_days" :min="1" :max="730" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="generate" :loading="genLoading">生成</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-form :inline="true" :model="filter" @submit.prevent>
        <el-form-item label="批次号">
          <el-input v-model="filter.batch_id" placeholder="精确匹配" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" clearable style="width: 120px">
            <el-option label="未用" value="unused" />
            <el-option label="已用" value="used" />
            <el-option label="作废" value="revoked" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load(1)">查询</el-button>
          <el-button v-if="filter.batch_id" @click="exportCsv">导出 CSV</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="codes" v-loading="loading" stripe>
        <el-table-column prop="code_mask" label="兑换码(脱敏)" width="200" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ typeName(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="points" label="积分" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="batch_id" label="批次号" width="180" />
        <el-table-column prop="user_id" label="使用者 ID" width="100" />
        <el-table-column prop="used_at" label="使用时间" width="170">
          <template #default="{ row }">{{ row.used_at ? formatTime(row.used_at) : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'unused'" size="small" type="danger" @click="revoke(row)">作废</el-button>
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

    <!-- 生成结果弹窗 -->
    <el-dialog v-model="genDialog" title="生成成功 - 请立即保存" width="600px">
      <el-alert type="warning" :closable="false">这些码只会显示这一次,关闭后无法找回,请复制到安全地方</el-alert>
      <el-input
        type="textarea"
        v-model="genResultText"
        :rows="10"
        readonly
        class="mt-16"
        style="font-family: monospace"
      />
      <el-button class="mt-16" @click="copyCodes">一键复制</el-button>
      <el-button @click="downloadTxt">下载 .txt</el-button>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminCodeApi } from '../api'

const genForm = ref({ type: 'single', count: 10, valid_days: 365 })
const genLoading = ref(false)
const genDialog = ref(false)
const genResult = ref<any>(null)
const genResultText = computed(() => genResult.value?.codes?.join('\n') || '')

const filter = ref<any>({ batch_id: '', status: '', page: 1, page_size: 50 })
const codes = ref<any[]>([])
const total = ref(0)
const loading = ref(false)

function typeName(t: string) {
  return { single: '次卡', monthly: '月卡', points_1000: '增购', trial: '试用' }[t] || t
}
function statusText(s: string) {
  return { unused: '未用', used: '已用', revoked: '作废' }[s] || s
}
function statusType(s: string) {
  return { used: 'success', revoked: 'danger' }[s] || 'info'
}
function formatTime(s: string) {
  return s ? new Date(s).toLocaleString('zh-CN') : '-'
}

async function generate() {
  genLoading.value = true
  try {
    const data: any = await adminCodeApi.generate(genForm.value.type, genForm.value.count, genForm.value.valid_days)
    genResult.value = data
    genDialog.value = true
    ElMessage.success(`已生成 ${data.count} 个码`)
    await load(1)
  } finally {
    genLoading.value = false
  }
}

async function copyCodes() {
  try {
    await navigator.clipboard.writeText(genResultText.value)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败,请手动复制')
  }
}

function downloadTxt() {
  const blob = new Blob([genResultText.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `redeem_${genResult.value?.batch_id || 'codes'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

async function load(page?: number) {
  if (page) filter.value.page = page
  loading.value = true
  try {
    const data: any = await adminCodeApi.list(filter.value)
    codes.value = data.items || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function revoke(row: any) {
  try {
    await ElMessageBox.confirm(`确定作废 ${row.code_mask}?`, '提示')
    await adminCodeApi.revoke(row.id)
    ElMessage.success('已作废')
    await load()
  } catch (e) {}
}

function exportCsv() {
  window.open(adminCodeApi.exportUrl(filter.value.batch_id), '_blank')
}

onMounted(() => load(1))
</script>

<style scoped>
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
h2 { margin: 0 0 16px; }
</style>
