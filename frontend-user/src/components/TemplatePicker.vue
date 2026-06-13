<template>
  <div class="template-picker">
    <div class="picker-label">简历模板</div>
    <div class="template-grid">
      <div
        v-for="t in templates"
        :key="t.code"
        class="template-card"
        :class="{ active: modelValue === t.code }"
        @click="$emit('update:modelValue', t.code)"
      >
        <div class="card-header">
          <div class="dot" :class="`dot-${t.code}`"></div>
          <div class="card-name">{{ t.display_name }}</div>
          <van-icon
            v-if="modelValue === t.code"
            name="success"
            class="check-icon"
            color="#1989fa"
            size="18"
          />
        </div>
        <div class="card-desc">{{ t.description }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { rewriteApi } from '../api/rewrite'

defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const templates = ref<Array<{ code: string; display_name: string; description: string }>>([])

onMounted(async () => {
  try {
    const data: any = await rewriteApi.templates()
    templates.value = data.templates || []
  } catch (e) {
    // 失败时给一个默认 classic,不让 UI 卡死
    templates.value = [
      {
        code: 'classic',
        display_name: '经典专业',
        description: '黑灰白配色 + 居中标题,适合国企/金融/传统行业',
      },
    ]
  }
})
</script>

<style scoped>
.template-picker {
  margin-bottom: 12px;
}

.picker-label {
  display: block;
  font-size: 13px;
  color: #646566;
  margin-bottom: 6px;
}

.template-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-card {
  border: 1.5px solid #ebedf0;
  border-radius: 8px;
  padding: 10px 12px;
  background: white;
  cursor: pointer;
  transition: all 0.15s;
}

.template-card.active {
  border-color: #1989fa;
  background: #f0f8ff;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-classic { background: #1a1a1a; }
.dot-modern { background: #2563eb; }
.dot-sidebar { background: #1e293b; }

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  flex: 1;
}

.check-icon {
  flex-shrink: 0;
}

.card-desc {
  font-size: 12px;
  color: #969799;
  line-height: 1.5;
  padding-left: 18px;
}
</style>
