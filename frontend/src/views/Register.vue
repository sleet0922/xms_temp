<template>
  <div class="neo-auth min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <Card padding="large">
        <div class="text-center mb-6">
          <div class="neo-brand-mark inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-3 group transition-all duration-200 ease-out hover:scale-105">
            <UserPlusIcon class="w-8 h-8 text-[#2f6f68] transition-colors duration-200" aria-hidden="true" />
          </div>
          <h1 class="text-2xl font-semibold tracking-tight text-gray-900">读者注册</h1>
          <p class="text-sm text-gray-500 mt-1">免费申请图书馆借阅证</p>
        </div>

        <form @submit.prevent="handleRegister">
          <div class="space-y-4">
            <Input
              v-model="form.username"
              label="用户名"
              placeholder="3 位以上字符"
              autocomplete="username"
              name="username"
              :prepend-icon="UserIcon"
              :error="errors.username"
              required
            />

            <Input
              v-model="form.full_name"
              label="真实姓名"
              placeholder="请输入真实姓名"
              autocomplete="name"
              name="name"
              :prepend-icon="IdentificationIcon"
              :error="errors.full_name"
              required
            />

            <Input
              v-model="form.email"
              label="电子邮箱"
              type="email"
              placeholder="your@example.com"
              autocomplete="email"
              name="email"
              :prepend-icon="EnvelopeIcon"
              :error="errors.email"
              required
            />

            <Input
              v-model="form.phone"
              label="联系电话"
              type="tel"
              placeholder="手机号码（可选）"
              autocomplete="tel"
              name="tel"
              :prepend-icon="PhoneIcon"
            />

            <Input
              v-model="form.card_number"
              label="借阅卡号"
              placeholder="留空则由系统自动生成"
              :prepend-icon="CreditCardIcon"
              hint="选填，自定义借阅证编号"
            />

            <Input
              v-model="form.password"
              label="登录密码"
              :type="showPassword ? 'text' : 'password'"
              placeholder="至少 6 位字符"
              autocomplete="new-password"
              name="new-password"
              :prepend-icon="LockClosedIcon"
              :append-icon="showPassword ? EyeIcon : EyeSlashIcon"
              :append-label="showPassword ? '隐藏密码' : '显示密码'"
              @append-click="showPassword = !showPassword"
              :error="errors.password"
              required
            />

            <Input
              v-model="form.confirmPassword"
              label="确认密码"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请再次输入密码"
              autocomplete="new-password"
              name="confirm-password"
              :prepend-icon="LockClosedIcon"
              :error="errors.confirmPassword"
              required
            />
          </div>

          <div class="mt-4">
            <Alert v-if="error" variant="error" :message="error" />
          </div>

          <div class="mt-4">
            <Button type="submit" variant="primary" size="large" block :loading="loading">
              提交注册
            </Button>
          </div>
        </form>

        <div class="mt-6 text-center text-sm text-gray-600">
          已有账号？
          <RouterLink
            to="/login"
            class="text-blue-600 hover:text-blue-700 font-medium rounded transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            去登录
          </RouterLink>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  CreditCardIcon,
  EnvelopeIcon,
  EyeIcon,
  EyeSlashIcon,
  IdentificationIcon,
  LockClosedIcon,
  PhoneIcon,
  UserIcon,
  UserPlusIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  full_name: '',
  email: '',
  phone: '',
  card_number: ''
})

const errors = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  full_name: '',
  email: ''
})

const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const validate = () => {
  Object.keys(errors).forEach(key => { errors[key] = '' })

  const username = form.username.trim()
  if (username.length < 3 || username.length > 20) {
    errors.username = '用户名长度需为 3-20 位字符'
  } else if (!/^[A-Za-z0-9_]+$/.test(username)) {
    errors.username = '用户名仅支持字母、数字与下划线'
  }

  if (!form.full_name.trim()) {
    errors.full_name = '请输入真实姓名'
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errors.email = '请输入有效的邮箱地址'
  }

  if (form.password.length < 6) {
    errors.password = '密码至少 6 位字符'
  }

  if (form.confirmPassword !== form.password) {
    errors.confirmPassword = '两次输入的密码不一致'
  }

  return Object.values(errors).every(message => !message)
}

const handleRegister = async () => {
  if (!validate()) return

  error.value = ''
  loading.value = true
  try {
    await userStore.register({
      username: form.username.trim(),
      password: form.password,
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || null,
      card_number: form.card_number.trim() || null
    })
    window.$toast?.success('注册成功，请使用新账号登录')
    router.push('/login')
  } catch (err) {
    error.value = err.response?.data?.detail || '注册失败，用户名或邮箱可能已被使用'
  } finally {
    loading.value = false
  }
}
</script>
