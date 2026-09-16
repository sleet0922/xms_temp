<template>
  <div id="app">
    <Toast ref="toastRef" />
    <router-view />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Toast from '@/components/ui/Toast.vue'
import { useToast } from '@/composables/useToast'

const toastRef = ref(null)
const toast = useToast()

onMounted(() => {
  toast.setInstance(toastRef.value)

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
