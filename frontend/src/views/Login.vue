<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <Card padding="large">
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-blue-50 mb-3 group transition-all duration-200 ease-out hover:bg-blue-500 hover:scale-110">
            <BuildingLibraryIcon class="w-8 h-8 text-blue-600 transition-colors duration-200 group-hover:text-white" aria-hidden="true" />
          </div>
          <h1 class="text-2xl font-semibold tracking-tight text-gray-900">智慧云图书馆</h1>
          <p class="text-sm text-gray-500 mt-1">登录以使用馆藏检索与借阅服务</p>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="space-y-4">
            <Input
              v-model="username"
              label="用户名"
              placeholder="请输入用户名"
              :prepend-icon="UserIcon"
              required
            />

            <Input
              v-model="password"
              label="密码"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              :prepend-icon="LockClosedIcon"
              :append-icon="showPassword ? EyeIcon : EyeSlashIcon"
              @append-click="showPassword = !showPassword"
              required
            />
          </div>

          <div class="mt-4">
            <Alert v-if="error" variant="error" :message="error" />
          </div>

          <div class="mt-4">
            <Button type="submit" variant="primary" size="large" block :loading="loading">
              登 录
            </Button>
          </div>
        </form>

        <div class="mt-6 text-center text-sm text-gray-600">
          还没有账号？
          <RouterLink
            to="/register"
            class="text-blue-600 hover:text-blue-700 font-medium rounded transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            立即注册
          </RouterLink>
        </div>

        <p class="mt-4 text-xs text-gray-500 text-center">
          演示账号：admin / librarian / student，密码 admin123
        </p>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  BuildingLibraryIcon,
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  UserIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
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
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>