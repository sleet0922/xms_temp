<template>
  <div class="neo-auth auth-layout auth-layout-single">
    <main class="auth-main">
      <div class="auth-form">
        <h1 class="text-[26px] font-semibold tracking-tight text-gray-900">账号登录</h1>
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
            class="text-[#2f5b4e] hover:text-[#487a69]"
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
import {
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  UserIcon
} from '@heroicons/vue/24/outline'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'

const router = useRouter()
const userStore = useUserStore()

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
