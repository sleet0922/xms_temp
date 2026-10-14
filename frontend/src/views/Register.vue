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
        <h2 class="text-[32px] font-semibold leading-tight">申请你的电子借阅证</h2>
        <p class="mt-4 text-[15px] leading-7 text-white/60">注册后即可在线借阅、预约排队，并接收到期与预约到书提醒。</p>
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
        <h1 class="text-2xl font-semibold text-gray-900">读者注册</h1>
        <p class="mt-2 mb-8 text-sm text-gray-500">填写以下信息，免费申请借阅证</p>
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
            <Button type="submit" variant="primary" block :loading="loading">
              提交注册
            </Button>
          </div>
        </form>

        <div class="mt-4 text-sm text-gray-500">
          已有账号？
          <RouterLink
            to="/login"
            class="text-[#165dff] hover:text-[#4080ff]"
          >
            去登录
          </RouterLink>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSystemStore } from '@/stores/system'
import {
  CreditCardIcon,
  EnvelopeIcon,
  EyeIcon,
  EyeSlashIcon,
  IdentificationIcon,
  LockClosedIcon,
  PhoneIcon,
  UserIcon,
  BuildingLibraryIcon
} from '@heroicons/vue/24/outline'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'

const systemStore = useSystemStore()
const year = new Date().getFullYear()
const highlights = [
  { value: '7×24', label: '在线检索' },
  { value: '一键', label: '续借预约' },
  { value: '实时', label: '到期提醒' }
]

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
