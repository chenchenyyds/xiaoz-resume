<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
import { useUserStore } from './stores/user'
import { onMounted } from 'vue'

const userStore = useUserStore()
onMounted(() => {
  // 应用启动时尝试拉取用户信息
  if (userStore.token && !userStore.user) {
    userStore.fetchMe().catch(() => {})
  }
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
