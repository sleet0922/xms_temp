<template>
  <div class="p-6 lg:p-8 max-w-7xl mx-auto">
    <PageHeader title="个人中心与借书卡" subtitle="借书卡信息、个人资料维护、密码修改与我的书评" />

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 左列：借书卡 + 借阅摘要 -->
      <div class="space-y-6">
        <Card padding="normal">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-full bg-blue-600 text-white text-2xl font-semibold flex items-center justify-center flex-shrink-0">
              {{ initial }}
            </div>
            <div class="min-w-0">
              <h2 class="text-lg font-semibold tracking-tight text-gray-900 truncate">
                {{ user?.full_name || user?.username || '未登录' }}
              </h2>
              <p class="text-sm text-gray-600 truncate">@{{ user?.username || '-' }}</p>
              <Badge :variant="roleMeta.variant" size="small" class="mt-2">{{ roleMeta.label }}</Badge>
            </div>
          </div>

          <dl class="mt-6 pt-6 border-t border-gray-200 space-y-3">
            <div class="flex items-center justify-between gap-4">
              <dt class="text-sm text-gray-500">借书卡号</dt>
              <dd class="text-sm font-medium text-gray-900 font-mono">{{ user?.card_number || '—' }}</dd>
            </div>
            <div class="flex items-center justify-between gap-4">
              <dt class="text-sm text-gray-500">注册时间</dt>
              <dd class="text-sm font-medium text-gray-900">{{ formatDate(user?.created_at) }}</dd>
            </div>
            <div class="flex items-center justify-between gap-4">
              <dt class="text-sm text-gray-500">电子邮箱</dt>
              <dd class="text-sm font-medium text-gray-900 truncate">{{ user?.email || '—' }}</dd>
            </div>
            <div class="flex items-center justify-between gap-4">
              <dt class="text-sm text-gray-500">联系电话</dt>
              <dd class="text-sm font-medium text-gray-900">{{ user?.phone || '—' }}</dd>
            </div>
          </dl>
        </Card>

        <Card padding="normal">
          <h3 class="text-lg font-semibold tracking-tight text-gray-900">借阅摘要</h3>
          <p class="text-sm text-gray-600 mt-1">实时统计我的借阅与费用状态</p>

          <div class="mt-5 space-y-4">
            <div v-for="item in summaryItems" :key="item.label" class="group flex items-center gap-3">
              <div
                :class="[
                  'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-200 ease-out group-hover:scale-110',
                  item.bg,
                  item.hover
                ]"
              >
                <component :is="item.icon" :class="['w-5 h-5 transition-colors duration-200', item.color, 'group-hover:text-white']" />
              </div>
              <div class="min-w-0">
                <div class="text-xs text-gray-500">{{ item.label }}</div>
                <div class="text-sm font-semibold text-gray-900">{{ item.value }}</div>
              </div>
            </div>
          </div>

          <p v-if="summaryLoading" class="text-xs text-gray-500 mt-4">加载中…</p>
        </Card>
      </div>

      <!-- 右列：资料编辑 / 修改密码 / 我的书评 -->
      <div class="lg:col-span-2">
        <Card padding="normal">
          <Tabs v-model="activeTab" :tabs="['资料编辑', '修改密码', '我的书评']">
            <!-- 资料编辑 -->
            <template #panel-0>
              <form class="space-y-4" @submit.prevent="handleUpdateProfile">
                <Input
                  v-model="profileForm.full_name"
                  label="姓名"
                  placeholder="请输入真实姓名"
                  :prepend-icon="UserIcon"
                  :error="profileErrors.full_name"
                  required
                />
                <Input
                  v-model="profileForm.email"
                  label="电子邮箱"
                  type="email"
                  placeholder="name@example.com"
                  :prepend-icon="EnvelopeIcon"
                  :error="profileErrors.email"
                  hint="用于账号找回与到期提醒"
                  required
                />
                <Input
                  v-model="profileForm.phone"
                  label="联系电话"
                  placeholder="选填"
                  :prepend-icon="PhoneIcon"
                  :error="profileErrors.phone"
                  hint="便于服务台联系，选填"
                />

                <Alert v-if="profileError" variant="error" :message="profileError" />

                <div class="flex justify-end">
                  <Button type="submit" variant="primary" :loading="profileSaving">保存资料</Button>
                </div>
              </form>
            </template>

            <!-- 修改密码 -->
            <template #panel-1>
              <form class="space-y-4" @submit.prevent="handleChangePassword">
                <Input
                  v-model="passwordForm.old_password"
                  label="当前密码"
                  type="password"
                  :prepend-icon="LockClosedIcon"
                  :error="passwordErrors.old_password"
                  required
                />
                <Input
                  v-model="passwordForm.new_password"
                  label="新密码"
                  type="password"
                  :prepend-icon="LockClosedIcon"
                  :error="passwordErrors.new_password"
                  hint="至少 6 位字符"
                  required
                />
                <Input
                  v-model="passwordForm.confirm_password"
                  label="确认新密码"
                  type="password"
                  :prepend-icon="LockClosedIcon"
                  :error="passwordErrors.confirm_password"
                  required
                />

                <Alert v-if="passwordError" variant="error" :message="passwordError" />

                <div class="flex justify-end">
                  <Button type="submit" variant="primary" :loading="passwordSaving">确认修改</Button>
                </div>
              </form>
            </template>

            <!-- 我的书评 -->
            <template #panel-2>
              <div v-if="reviewsLoading" class="py-12 text-center text-sm text-gray-500">加载中…</div>

              <EmptyState
                v-else-if="reviews.length === 0"
                title="暂无书评"
                description="在图书详情页为读过的书写下评分与感想，会显示在这里。"
                :icon="ChatBubbleLeftRightIcon"
              />

              <div v-else class="divide-y divide-gray-200">
                <div v-for="review in reviews" :key="review.id" class="py-4 first:pt-0 last:pb-0">
                  <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                    <div class="min-w-0">
                      <h4 class="font-semibold tracking-tight text-gray-900 truncate">
                        {{ review.book?.title || `图书 #${review.book_id}` }}
                      </h4>
                      <div class="mt-2">
                        <RatingStars :model-value="review.rating" size="small" />
                      </div>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0">
                      <Button size="small" variant="outline" @click="goBookDetail(review)">查看详情</Button>
                      <Button size="small" variant="ghost" @click="openDeleteDialog(review)">删除</Button>
                    </div>
                  </div>

                  <p v-if="review.content" class="text-sm text-gray-600 mt-3">{{ review.content }}</p>
                  <p class="text-xs text-gray-500 mt-2">更新于 {{ formatDateTime(review.updated_at) }}</p>
                </div>
              </div>
            </template>
          </Tabs>
        </Card>
      </div>
    </div>

    <!-- 删除书评确认 -->
    <Dialog v-model="showDeleteDialog" title="删除书评" max-width="sm">
      <p class="text-sm text-gray-600">
        确认删除《{{ deleteTarget?.book?.title || `图书 #${deleteTarget?.book_id}` }}》的书评？删除后不可恢复。
      </p>
      <template #footer>
        <Button variant="outline" @click="showDeleteDialog = false">取消</Button>
        <Button variant="danger" :loading="deleting" @click="handleDeleteReview">确认删除</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  BanknotesIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  EnvelopeIcon,
  ExclamationTriangleIcon,
  LockClosedIcon,
  PhoneIcon,
  UserIcon
} from '@heroicons/vue/24/outline'
import PageHeader from '@/components/ui/PageHeader.vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Alert from '@/components/ui/Alert.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Tabs from '@/components/ui/Tabs.vue'
import RatingStars from '@/components/ui/RatingStars.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { authApi, statsApi, reservationsApi, reviewsApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const user = computed(() => userStore.user)

const ROLE_META = {
  admin: { label: '系统管理员', variant: 'primary' },
  librarian: { label: '服务台馆员', variant: 'success' },
  reader: { label: '普通读者', variant: 'default' }
}

const activeTab = ref(0)

const overview = ref({ user_borrowed: 0, user_overdue: 0, user_fines: '0.00' })
const reservationCount = ref(0)
const summaryLoading = ref(false)

const reviews = ref([])
const reviewsLoading = ref(false)
const showDeleteDialog = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)

const profileForm = reactive({ full_name: '', email: '', phone: '' })
const profileErrors = reactive({ full_name: '', email: '', phone: '' })
const profileError = ref('')
const profileSaving = ref(false)

const passwordForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const passwordErrors = reactive({ old_password: '', new_password: '', confirm_password: '' })
const passwordError = ref('')
const passwordSaving = ref(false)

const initial = computed(() => (user.value?.full_name || user.value?.username || '?').charAt(0).toUpperCase())
const roleMeta = computed(() => ROLE_META[user.value?.role] || ROLE_META.reader)

const money = (value) => Number(value || 0).toFixed(2)

const summaryItems = computed(() => [
  {
    label: '在借图书',
    value: `${overview.value.user_borrowed || 0} 本`,
    icon: BookOpenIcon,
    bg: 'bg-blue-50',
    hover: 'group-hover:bg-blue-500',
    color: 'text-blue-600'
  },
  {
    label: '逾期未还',
    value: `${overview.value.user_overdue || 0} 本`,
    icon: ExclamationTriangleIcon,
    bg: 'bg-red-50',
    hover: 'group-hover:bg-red-500',
    color: 'text-red-600'
  },
  {
    label: '未缴罚金',
    value: `¥${money(overview.value.user_fines)}`,
    icon: BanknotesIcon,
    bg: 'bg-amber-50',
    hover: 'group-hover:bg-amber-500',
    color: 'text-amber-600'
  },
  {
    label: '预约中',
    value: `${reservationCount.value} 本`,
    icon: ClockIcon,
    bg: 'bg-green-50',
    hover: 'group-hover:bg-green-500',
    color: 'text-green-600'
  }
])

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${date.toLocaleDateString('zh-CN')} ${hh}:${mm}`
}

const syncProfileForm = (currentUser) => {
  if (!currentUser) return
  profileForm.full_name = currentUser.full_name || ''
  profileForm.email = currentUser.email || ''
  profileForm.phone = currentUser.phone || ''
}

watch(user, (value) => syncProfileForm(value), { immediate: true })

const loadSummary = async () => {
  summaryLoading.value = true
  try {
    const [overviewRes, reservationRes] = await Promise.all([
      statsApi.getOverview(),
      reservationsApi.getList()
    ])
    overview.value = overviewRes.data
    // 馆员/管理员调用该接口会返回全馆预约，这里仅统计本人记录
    reservationCount.value = reservationRes.data.filter(
      (item) =>
        item.user_id === user.value?.id &&
        (item.status === 'waiting' || item.status === 'notified')
    ).length
  } catch (err) {
    window.$toast?.error('加载借阅摘要失败')
  } finally {
    summaryLoading.value = false
  }
}

const loadMyReviews = async () => {
  reviewsLoading.value = true
  try {
    const response = await reviewsApi.getMine()
    reviews.value = response.data
  } catch (err) {
    window.$toast?.error('加载我的书评失败')
  } finally {
    reviewsLoading.value = false
  }
}

const validateProfile = () => {
  profileErrors.full_name = profileForm.full_name.trim() ? '' : '姓名不能为空'
  profileErrors.email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileForm.email.trim())
    ? ''
    : '请输入有效的电子邮箱'
  profileErrors.phone =
    !profileForm.phone.trim() || /^[\d\s+\-]{6,20}$/.test(profileForm.phone.trim())
      ? ''
      : '请输入有效的联系电话'
  return !profileErrors.full_name && !profileErrors.email && !profileErrors.phone
}

const handleUpdateProfile = async () => {
  profileError.value = ''
  if (!validateProfile()) return

  profileSaving.value = true
  try {
    // 后端 PUT /auth/profile 仅接受并写入 full_name / email / phone
    await authApi.updateProfile({
      full_name: profileForm.full_name.trim(),
      email: profileForm.email.trim(),
      phone: profileForm.phone.trim() || null
    })
    await userStore.fetchUserInfo()
    window.$toast?.success('个人资料已更新')
  } catch (err) {
    profileError.value = err.response?.data?.detail || '资料更新失败'
  } finally {
    profileSaving.value = false
  }
}

const handleChangePassword = async () => {
  passwordError.value = ''
  passwordErrors.old_password = passwordForm.old_password ? '' : '请输入当前密码'
  passwordErrors.new_password = passwordForm.new_password.length >= 6 ? '' : '新密码至少 6 位字符'
  passwordErrors.confirm_password =
    passwordForm.confirm_password === passwordForm.new_password && passwordForm.confirm_password
      ? ''
      : '两次输入的新密码不一致'
  if (passwordErrors.old_password || passwordErrors.new_password || passwordErrors.confirm_password) return

  passwordSaving.value = true
  try {
    await authApi.changePassword(passwordForm.old_password, passwordForm.new_password)
    window.$toast?.success('密码修改成功，请妥善保管')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (err) {
    passwordError.value = err.response?.data?.detail || '密码修改失败'
  } finally {
    passwordSaving.value = false
  }
}

const goBookDetail = (review) => {
  router.push(`/books/${review.book_id}`)
}

const openDeleteDialog = (review) => {
  deleteTarget.value = review
  showDeleteDialog.value = true
}

const handleDeleteReview = async () => {
  deleting.value = true
  try {
    await reviewsApi.remove(deleteTarget.value.id)
    window.$toast?.success('书评已删除')
    showDeleteDialog.value = false
    await loadMyReviews()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  loadSummary()
  loadMyReviews()
})
</script>