<template>
  <div class="rewrite-panel">
    <div class="panel-header">
      <div class="title">完整改写 · 1000 积分/1500 积分(含 JD)</div>
      <van-icon name="cross" size="20" @click="$emit('close')" />
    </div>

    <div class="panel-body">
      <div class="form-item">
        <label>选择简历</label>
        <van-radio-group v-model="selectedFileId" v-if="files.length > 0">
          <van-cell-group inset>
            <van-cell
              v-for="f in files"
              :key="f.id"
              clickable
              @click="selectedFileId = f.id"
            >
              <template #title>
                <van-radio :name="f.id" />
                <span style="margin-left: 8px">{{ f.file_name }}</span>
              </template>
            </van-cell>
          </van-cell-group>
        </van-radio-group>
        <van-empty v-else description="还没有上传简历" :image-size="60" />
        <div class="mt-8 text-center">
          <van-button size="small" plain @click="goUpload">去上传 ›</van-button>
        </div>
      </div>

      <div class="form-item">
        <label>
          目标 JD(选填,粘贴职位描述)
          <span class="text-placeholder" style="font-weight: normal; font-size: 12px">
            · 含 JD 1500 积分,不含 1000 积分
          </span>
        </label>
        <van-field
          v-model="jdText"
          type="textarea"
          rows="5"
          autosize
          placeholder="把 JD 内容粘贴到这里,AI 会针对性优化你的简历"
          maxlength="8000"
          show-word-limit
        />
      </div>

      <div class="form-item">
        <label>风格要求(选填)</label>
        <van-field v-model="styleHint" placeholder="如:突出技术深度 / 突出管理能力" />
      </div>

      <van-button
        block
        round
        type="primary"
        :loading="loading"
        :disabled="!canSubmit"
        @click="submit"
      >
        {{ costText }}
      </van-button>

      <div v-if="result" class="result mt-16">
        <div class="result-title flex-between">
          <span>改写完成 ✓</span>
          <a v-if="result.file_url" :href="result.file_url" target="_blank" class="text-primary" style="font-size: 12px">
            下载 docx
          </a>
        </div>
        <div class="result-content">{{ result.output_text }}</div>

        <div v-if="result.improvement_points?.length" class="mt-12">
          <div class="result-sub-title">📋 优化点</div>
          <ol class="points-list">
            <li v-for="(p, i) in result.improvement_points" :key="i">{{ p }}</li>
          </ol>
        </div>

        <div class="result-footer">
          消耗 {{ result.points_cost }} 积分 · 剩余 {{ result.points_remaining }} 积分
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { rewriteApi } from '../api/rewrite'
import { fileApi } from '../api/files'

const emit = defineEmits(['close', 'done'])
const router = useRouter()

const files = ref<any[]>([])
const selectedFileId = ref<number | null>(null)
const jdText = ref('')
const styleHint = ref('')
const loading = ref(false)
const result = ref<any>(null)

const canSubmit = computed(() => selectedFileId.value !== null)

const costText = computed(() => {
  return jdText.value.trim() ? '开始改写(1500 积分)' : '开始改写(1000 积分)'
})

async function loadFiles() {
  const data: any = await fileApi.list()
  files.value = data.items || []
  if (files.value.length > 0) selectedFileId.value = files.value[0].id
}

function goUpload() {
  emit('close')
  router.push('/files')
}

async function submit() {
  loading.value = true
  try {
    const data: any = await rewriteApi.full(
      selectedFileId.value!,
      jdText.value || undefined,
      styleHint.value || undefined
    )
    result.value = data
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

onMounted(loadFiles)
</script>

<style scoped>
.rewrite-panel {
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

.title {
  font-size: 16px;
  font-weight: 600;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  font-size: 13px;
  color: #646566;
  margin-bottom: 6px;
}

.result {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
}

.result-title {
  font-size: 14px;
  font-weight: 600;
  color: #1989fa;
  margin-bottom: 8px;
}

.result-sub-title {
  font-size: 13px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 6px;
}

.result-content {
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: #323233;
  max-height: 400px;
  overflow-y: auto;
}

.points-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 1.7;
  color: #323233;
}

.points-list li {
  margin-bottom: 4px;
}

.result-footer {
  margin-top: 8px;
  font-size: 12px;
  color: #969799;
  text-align: right;
}

.text-center { text-align: center; }
</style>
