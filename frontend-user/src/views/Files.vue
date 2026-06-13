<template>
  <div class="page">
    <div class="card">
      <div class="flex-between mb-12">
        <div class="section-title">我的简历</div>
        <van-button size="small" type="primary" @click="showUpload = true">上传新简历</van-button>
      </div>
      <van-empty v-if="files.length === 0" description="还没有上传简历" />
      <div v-else class="file-list">
        <div v-for="f in files" :key="f.id" class="file-row">
          <div class="file-info">
            <div class="file-name">{{ f.file_name }}</div>
            <div class="text-placeholder" style="font-size: 12px">
              {{ formatSize(f.file_size) }} · {{ formatTime(f.created_at) }}
              <van-tag v-if="f.type === 'generated'" type="success" size="mini" style="margin-left: 4px">AI 生成</van-tag>
            </div>
          </div>
          <div class="file-actions">
            <van-button size="mini" plain @click="useForRewrite(f)">改写</van-button>
            <van-button size="mini" plain type="danger" @click="confirmDelete(f)">删除</van-button>
          </div>
        </div>
      </div>
    </div>

    <van-tabbar v-model="tabActive" route>
      <van-tabbar-item to="/workbench" icon="home-o">工作台</van-tabbar-item>
      <van-tabbar-item to="/files" icon="orders-o">简历</van-tabbar-item>
      <van-tabbar-item to="/redeem" icon="coupon-o">兑换</van-tabbar-item>
      <van-tabbar-item to="/me" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>

    <!-- 上传弹窗 -->
    <van-popup v-model:show="showUpload" position="bottom" round :style="{ height: '40%' }">
      <div class="upload-panel">
        <div class="panel-header">
          <div class="title">上传简历</div>
          <van-icon name="cross" size="20" @click="showUpload = false" />
        </div>
        <div class="panel-body">
          <van-uploader :after-read="afterRead" :max-count="1" accept=".docx">
            <van-button block icon="plus">选择 docx 文件</van-button>
          </van-uploader>
          <div class="text-placeholder mt-12" style="font-size: 12px">
            仅支持 .docx 格式,最大 10MB
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { fileApi } from '../api/files'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const tabActive = ref(1)

const files = ref<any[]>([])
const showUpload = ref(false)

async function loadFiles() {
  const data: any = await fileApi.list()
  files.value = data.items || []
}

async function afterRead(file: any) {
  try {
    await fileApi.upload(file.file, file.file.name)
    showToast('上传成功')
    showUpload.value = false
    await loadFiles()
  } catch (e) {}
}

function useForRewrite(f: any) {
  if (f.type === 'generated') {
    showToast('生成结果不能直接改写,请上传新简历')
    return
  }
  // 跳到工作台,带 file_id 参数
  router.push({ path: '/workbench', query: { file_id: f.id } })
}

async function confirmDelete(f: any) {
  try {
    await showDialog({ title: '确认删除', message: `删除「${f.file_name}」?` })
    await fileApi.remove(f.id)
    showToast('已删除')
    await loadFiles()
  } catch (e) {}
}

function formatSize(b: number) {
  if (!b) return '-'
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / 1024 / 1024).toFixed(1)} MB`
}

function formatTime(s: string) {
  const d = new Date(s)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}

onMounted(async () => {
  if (!userStore.user) await userStore.fetchMe()
  await loadFiles()
})
</script>

<style scoped>
.section-title { font-size: 15px; font-weight: 600; }
.file-list { display: flex; flex-direction: column; gap: 8px; }
.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f2f3f5;
}
.file-row:last-child { border-bottom: none; }
.file-info { flex: 1; min-width: 0; }
.file-name {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-actions { display: flex; gap: 6px; flex-shrink: 0; }

.upload-panel { height: 100%; display: flex; flex-direction: column; background: white; }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebedf0;
}
.title { font-size: 16px; font-weight: 600; }
.panel-body { flex: 1; overflow-y: auto; padding: 20px 16px; }
</style>
