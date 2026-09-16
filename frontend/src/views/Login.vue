<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="w-full max-w-md">
      <Card padding="large">
        <!-- Header -->
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-blue-50 mb-3">
            <BuildingLibraryIcon class="w-9 h-9 text-blue-600" aria-hidden="true" />
          </div>
          <h2 class="text-2xl font-bold text-gray-900">未来智慧云图书馆</h2>
          <p class="text-sm text-gray-500 mt-1">Enterprise Library Management System</p>
        </div>

        <!-- Quick Fill Chips -->
        <div class="bg-gray-50 rounded-xl p-3 mb-5">
          <p class="text-xs font-semibold text-gray-600 mb-2 flex items-center">
            <UserIcon class="w-3.5 h-3.5 mr-1" />
            一键快速填入体验身份
          </p>
          <div class="flex flex-wrap gap-2">
            <Badge
              variant="danger"
              @click="fillCredentials('admin', 'admin123')"
              class="cursor-pointer hover:opacity-80 transition-opacity"
            >
              管理员 (admin)
            </Badge>
            <Badge
              variant="primary"
              @click="fillCredentials('librarian', 'admin123')"
              class="cursor-pointer hover:opacity-80 transition-opacity"
            >
              服务台馆员 (librarian)
            </Badge>
            <Badge
              variant="secondary"
              @click="fillCredentials('student', 'admin123')"
              class="cursor-pointer hover:opacity-80 transition-opacity"
            >
              在籍读者 (student)
            </Badge>
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin">
          <Input
            v-model="username"
            label="登录用户名"
            placeholder="请输入用户名"
            :prepend-icon="UserIcon"
            required
            class="mb-3"
          />

          <Input
            v-model="password"
            label="账户密码"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
            :prepend-icon="LockClosedIcon"
            :append-icon="showPassword ? EyeIcon : EyeSlashIcon"
            @append-click="showPassword = !showPassword"
            required
            class="mb-4"
          />

          <Alert v-if="error" variant="error" class="mb-4" :message="error" />

          <Button
            type="submit"
            variant="primary"
            size="large"
            block
            :loading="loading"
          >
            登 录 系 统
          </Button>

          <div class="text-center mt-4">
            <Button
              variant="ghost"
              size="small"
              @click="$router.push('/register')"
            >
              没有借阅证账号？免费注册读者卡
            </Button>
          </div>
        </form>
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
  UserIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Alert from '@/components/ui/Alert.vue'

const router = useRouter()
const userStore = useUserStore()

const username = ref('admin')
const password = ref('admin123')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

function fillCredentials(u, p) {
  username.value = u
  password.value = p
  error.value = ''
}

const handleLogin = async () => {
  error.value = ''
  loading.value = true
  try {
    await userStore.login(username.value, password.value)
    // Toast notification will be added later when App.vue is refactored
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>
