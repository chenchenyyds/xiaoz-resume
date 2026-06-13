<template>
  <div class="rewrite-panel">
    <div class="panel-header">
      <div class="title">部分改写 · 50 积分/次</div>
      <van-icon name="cross" size="20" @click="$emit('close')" />
    </div>

    <div class="panel-body">
      <div class="form-item">
        <label>板块标题(选填)</label>
        <van-field v-model="title" placeholder="如:工作经历、项目经验" />
      </div>

      <div class="form-item">
        <label>原文</label>
        <van-field
          v-model="text"
          type="textarea"
          rows="6"
          autosize
          placeholder="把要改写的简历片段粘贴在这里,至少 10 字"
          maxlength="3000"
          show-word-limit
        />
      </div>

      <div class="form-item">
        <label>风格要求(选填)</label>
        <van-field v-model="styleHint" placeholder="如:更口语化 / 更专业" />
      </div>

      <van-button
        block
        round
        type="primary"
        :loading="loading"
        :disabled="!canSubmit"
        @click="submit"
      >
        开始改写
      </van-button>

      <div v-if="result" class="result mt-16">
        <div class="result-title">改写结果</div>
        <div class="result-content">{{ result.output_text }}</div>
        <div class="result-explanation mt-8">
          💡 {{ result.explanation }}
        </div>
        <div class="result-footer">
          消耗 {{ result.points_cost }} 积分 · 剩余 {{ result.points_remaining }} 积分
        </div>
        <div class="mt-12">
          <van-button block plain type="primary" @click="copyResult">复制结果</van-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { showToast } from 'vant'
import { rewriteApi } from '../api/rewrite'

const emit = defineEmits(['close', 'done'])

const title = ref('')
const text = ref('')
const styleHint = ref('')
const loading = ref(false)
const result = ref<any>(null)

const canSubmit = computed(() => text.value.length >= 10)

async function submit() {
  loading.value = true
  try {
    const data: any = await rewriteApi.partial(text.value, title.value || undefined, styleHint.value || undefined)
    result.value = data
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

async function copyResult() {
  if (result.value?.output_text) {
    await navigator.clipboard.writeText(result.value.output_text)
    showToast('已复制')
    emit('done')
  }
}
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
  font-size: 13px;
  font-weight: 600;
  color: #1989fa;
  margin-bottom: 8px;
}

.result-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: #323233;
}

.result-explanation {
  font-size: 12px;
  color: #646566;
  background: white;
  padding: 8px;
  border-radius: 4px;
}

.result-footer {
  margin-top: 8px;
  font-size: 12px;
  color: #969799;
  text-align: right;
}
</style>
