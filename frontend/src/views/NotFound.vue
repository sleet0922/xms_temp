<template>
  <main class="flex min-h-[100dvh] items-center justify-center px-6 py-16">
    <div class="w-full max-w-md text-center">
      <p class="text-sm font-semibold tracking-wide text-[#2f5b4e]">404</p>
      <h1 class="mt-3 text-2xl font-semibold tracking-tight text-gray-900">页面不存在</h1>
      <p class="mt-3 text-sm text-gray-600">
        您访问的地址
        <code class="rounded bg-[#eeeae4] px-1.5 py-0.5 text-xs text-gray-700 break-all">{{ route.fullPath }}</code>
        不存在，可能已被移动或输入有误。
      </p>
      <div class="mt-8 flex flex-wrap justify-center gap-3">
        <Button variant="outline" @click="goBack">返回上一页</Button>
        <Button variant="primary" @click="router.replace(homePath)">{{ homeLabel }}</Button>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const homePath = computed(() => {
  if (!userStore.isAuthenticated) return '/login'
  return userStore.isLibrarian ? '/admin' : '/'
})
const homeLabel = computed(() => (userStore.isAuthenticated ? '回到首页' : '前往登录'))

function goBack() {
  // 直接打开无效地址时没有站内历史，退回首页
  if (window.history.state?.back) router.back()
  else router.replace(homePath.value)
}
</script>
