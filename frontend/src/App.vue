<template>
  <div id="app">
    <Toast ref="toastRef" />
    <router-view />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Toast from '@/components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'
import { useSystemStore } from '@/stores/system'

const toastRef = ref(null)
const toast = useToast()
const systemStore = useSystemStore()
const route = useRoute()

// 馆名改动后保持浏览器标题同步（路由切换时由路由守卫写入）
watch(
  () => [route.meta?.title, systemStore.libraryName],
  ([pageTitle, libraryName]) => {
    if (pageTitle) document.title = `${pageTitle} - ${libraryName}`
  }
)

onMounted(() => {
  toast.setInstance(toastRef.value)

  // 馆名与业务规则统一从后端公开配置读取（系统设置里改了立刻生效）
  systemStore.load()

  // Make toast globally available
  window.$toast = {
    success: toast.success,
    error: toast.error,
    warning: toast.warning,
    info: toast.info
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  min-height: 100vh;
  font-family: 'Inter var', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
