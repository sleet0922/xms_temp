<template>
  <div class="neo-auth auth-layout">
    <aside class="auth-aside">
      <div class="flex items-center gap-2.5 text-[15px] font-semibold">
        <span class="inline-flex h-7 w-7 items-center justify-center rounded bg-[#165dff]">
          <BuildingLibraryIcon class="h-4 w-4" aria-hidden="true" />
        </span>
        {{ systemStore.libraryName }}
      </div>
      <div class="max-w-md">
        <h2 class="text-[32px] font-semibold leading-tight">一站式馆藏检索与借阅服务</h2>
        <p class="mt-4 text-[15px] leading-7 text-white/60">查询馆藏、在线预约、管理借阅记录，随时掌握到期与通知。</p>
        <div class="mt-10 grid grid-cols-3 border-t border-white/15 pt-6">
          <div v-for="item in highlights" :key="item.label">
            <div class="text-xl font-semibold">{{ item.value }}</div>
            <div class="mt-1 text-xs text-white/50">{{ item.label }}</div>
          </div>
        </div>
      </div>
      <div class="text-xs text-white/40">© {{ year }} {{ systemStore.libraryName }}</div>
    </aside>
    <main class="auth-main">
      <div class="auth-form">
        <h1 class="text-2xl font-semibold text-gray-900">账号登录</h1>
        <p class="mt-2 mb-8 text-sm text-gray-500">欢迎回来，请使用图书馆账号登录</p>
        <form @submit.prevent="handleLogin">
          <div class="space-y-4">
            <Input
              v-model="username"
              label="用户名"
              placeholder="请输入用户名"
              autocomplete="username"
              name="username"
              :prepend-icon="UserIcon"
              required
            />

            <Input
              v-model="password"
              label="密码"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              autocomplete="current-password"
              name="password"
              :prepend-icon="LockClosedIcon"
              :append-icon="showPassword ? EyeIcon : EyeSlashIcon"
              :append-label="showPassword ? '隐藏密码' : '显示密码'"
              @append-click="showPassword = !showPassword"
              required
            />
          </div>

          <div class="mt-4">
            <Alert v-if="error" variant="error" :message="error" />
          </div>

          <div class="mt-4">
            <Button type="submit" variant="primary" block :loading="loading">
              登 录
            </Button>
          </div>
        </form>

        <div class="mt-4 text-sm text-gray-500">
          还没有账号？
          <RouterLink
            to="/register"
            class="text-[#165dff] hover:text-[#4080ff]"
          >
            立即注册
          </RouterLink>
        </div>

        <p class="mt-8 rounded bg-[#f7f8fa] px-3 py-2 text-xs text-gray-500">
          演示账号：admin / librarian / student，密码 admin123
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSystemStore } from '@/stores/system'
import {
  BuildingLibraryIcon,
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  UserIcon
} from '@heroicons/vue/24/outline'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'

const year = new Date().getFullYear()
const highlights = [
  { value: '7×24', label: '在线检索' },
  { value: '一键', label: '续借预约' },
  { value: '实时', label: '到期提醒' }
]

const router = useRouter()
const userStore = useUserStore()
const systemStore = useSystemStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  error.value = ''
  loading.value = true
  try {
    await userStore.login(username.value, password.value)
    window.$toast?.success('登录成功，欢迎回来')
    router.push(userStore.isLibrarian ? '/admin' : '/')
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>
