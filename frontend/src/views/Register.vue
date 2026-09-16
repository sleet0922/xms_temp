<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-8">
    <div class="w-full max-w-md">
      <Card padding="large">
        <!-- Header -->
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-blue-50 mb-3">
            <UserIcon class="w-9 h-9 text-blue-600" aria-hidden="true" />
          </div>
          <h2 class="text-2xl font-bold text-gray-900">读者注册</h2>
          <p class="text-sm text-gray-500 mt-1">免费申请图书馆借阅证</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleRegister">
          <Input
            v-model="form.username"
            label="用户名"
            placeholder="设置登录用户名"
            :prepend-icon="UserIcon"
            :error="errors.username"
            required
            class="mb-3"
          />

          <Input
            v-model="form.email"
            label="电子邮箱"
            type="email"
            placeholder="your@example.com"
            :prepend-icon="IdentificationIcon"
            :error="errors.email"
            required
            class="mb-3"
          />

          <Input
            v-model="form.full_name"
            label="真实姓名"
            placeholder="请输入真实姓名"
            :prepend-icon="IdentificationIcon"
            :error="errors.full_name"
            required
            class="mb-3"
          />

          <Input
            v-model="form.phone"
            label="联系电话"
            type="tel"
            placeholder="手机号码（可选）"
            :prepend-icon="IdentificationIcon"
            class="mb-3"
          />

          <Input
            v-model="form.password"
            label="登录密码"
            :type="showPassword ? 'text' : 'password'"
            placeholder="至少 6 位字符"
            :prepend-icon="LockClosedIcon"
            :append-icon="showPassword ? EyeIcon : EyeSlashIcon"
            @append-click="showPassword = !showPassword"
            :error="errors.password"
            required
            class="mb-4"
          />

          <Alert v-if="error" variant="error" class="mb-4" :message="error" />
          <Alert v-if="success" variant="success" class="mb-4" :message="success" />

          <Button
            type="submit"
            variant="primary"
            size="large"
            block
            :loading="loading"
          >
            提交注册申请
          </Button>

          <div class="text-center mt-4">
            <Button
              variant="ghost"
              size="small"
              @click="$router.push('/login')"
            >
              已有账号？立即登录
            </Button>
          </div>
        </form>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  UserIcon,
  IdentificationIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'
import { authApi } from '@/api'

const router = useRouter()

const form = reactive({
  username: '',
  email: '',
  full_name: '',
  phone: '',
  password: ''
})

const errors = reactive({
  username: '',
  email: '',
  full_name: '',
  password: ''
})

const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref('')

const validateForm = () => {
  errors.username = ''
  errors.email = ''
  errors.full_name = ''
  errors.password = ''

  if (form.username.length < 3) {
    errors.username = '用户名至少 3 位字符'
    return false
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = '请输入有效的邮箱地址'
    return false
  }

  if (form.full_name.length < 2) {
    errors.full_name = '请输入真实姓名'
    return false
  }

  if (form.password.length < 6) {
    errors.password = '密码至少 6 位字符'
    return false
  }

  return true
}

const handleRegister = async () => {
  if (!validateForm()) return

  error.value = ''
  success.value = ''
  loading.value = true

  try {
    await authApi.register(form)
    success.value = '注册成功！3 秒后自动跳转登录页...'
    setTimeout(() => {
      router.push('/login')
    }, 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || '注册失败，用户名或邮箱可能已存在'
  } finally {
    loading.value = false
  }
}
</script>
