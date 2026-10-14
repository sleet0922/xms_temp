<template>
  <div class="neo-page">
    <PageHeader title="用户管理" subtitle="读者档案、借书卡与借阅情况">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadReaders">
          刷新列表
        </Button>
        <Button v-if="userStore.isLibrarian" variant="primary" :prepend-icon="UserPlusIcon" @click="openCreate">
          新增读者
        </Button>
      </template>
    </PageHeader>

    <!-- 读者概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <StatCard
        label="注册读者总数"
        :value="overview.total_readers ?? 0"
        hint="角色为读者的账号总量"
        :icon="UsersIcon"
        tone="primary"
      />
      <StatCard
        label="当前在借读者"
        :value="activeReaderCount"
        :hint="`在借记录 ${overview.active_borrows ?? 0} 条`"
        :icon="BookOpenIcon"
        tone="success"
      />
      <StatCard
        label="黑名单 / 停用"
        :value="disabledCount"
        hint="状态非正常的读者账号"
        :icon="NoSymbolIcon"
        tone="danger"
      />
    </div>

    <!-- 检索与筛选 -->
    <Card class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          v-model="search"
          label="关键词"
          placeholder="姓名、用户名、卡号、邮箱、电话"
          :prepend-icon="MagnifyingGlassIcon"
        />
        <Select v-model="statusFilter" :options="statusOptions" label="账号状态" placeholder="全部状态" />
        <Select v-model="roleFilter" :options="roleOptions" label="角色" placeholder="全部角色" />
      </div>
    </Card>

    <!-- 读者列表 -->
    <Card padding="none">
      <div class="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-gray-200">
        <h2 class="text-base font-medium text-gray-900">读者列表</h2>
        <span class="text-xs text-gray-500">{{ loading ? '加载中…' : `共 ${readers.length} 位读者` }}</span>
      </div>

      <div v-if="loading" class="px-6 py-6 text-sm text-gray-500">正在加载读者档案…</div>

      <div v-else-if="readers.length" class="overflow-x-auto scrollbar-thin">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">姓名</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">用户名</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">卡号</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">邮箱</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">电话</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
              <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="reader in readers" :key="reader.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 text-sm font-medium text-gray-900">
                {{ reader.full_name || '-' }}
                <span v-if="reader.role && reader.role !== 'reader'" class="ml-2">
                  <Badge variant="secondary" size="small">{{ roleLabel(reader.role) }}</Badge>
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ reader.username }}</td>
              <td class="px-4 py-3 text-sm text-gray-600 font-mono">{{ reader.card_number || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{{ reader.email || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ reader.phone || '-' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="statusVariant(reader.status)" size="small">
                  {{ statusLabel(reader.status) }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right whitespace-nowrap">
                <Button size="small" variant="ghost" @click="openProfile(reader)">查看画像</Button>
                <Button size="small" variant="ghost" @click="openEdit(reader)">编辑</Button>
                <Button size="small" variant="ghost" @click="openResetPassword(reader)">重置密码</Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <EmptyState
        v-else
        title="没有匹配的读者"
        description="试试更换关键词，或调整状态与角色筛选条件"
        :icon="MagnifyingGlassIcon"
      />
    </Card>

    <!-- 读者画像 -->
    <Dialog v-model="showProfileDialog" title="读者画像" max-width="2xl" scrollable>
      <div v-if="profileLoading" class="py-8 text-sm text-gray-500 text-center">正在加载读者画像…</div>

      <div v-else-if="profile" class="space-y-6">
        <section>
          <h3 class="text-base font-medium text-gray-900 mb-3">基本信息</h3>
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            <div v-for="item in profileBasic" :key="item.label" class="flex items-center justify-between gap-4">
              <dt class="text-sm text-gray-500">{{ item.label }}</dt>
              <dd class="text-sm font-medium text-gray-900" :class="item.mono ? 'font-mono' : ''">{{ item.value }}</dd>
            </div>
          </dl>
        </section>

        <section class="pt-5 border-t border-gray-200">
          <h3 class="text-base font-medium text-gray-900 mb-3">借阅统计</h3>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
              <div class="text-xs text-gray-500">累计借阅</div>
              <div class="text-base font-medium text-gray-900 mt-1">{{ profile.total_borrows }}</div>
            </div>
            <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
              <div class="text-xs text-gray-500">当前在借</div>
              <div class="text-base font-medium text-gray-900 mt-1">{{ profile.active_borrows }}</div>
            </div>
            <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
              <div class="text-xs text-gray-500">逾期未还</div>
              <div
                class="text-xl font-semibold tracking-tight mt-1"
                :class="profile.overdue_borrows > 0 ? 'text-red-600' : 'text-gray-900'"
              >
                {{ profile.overdue_borrows }}
              </div>
            </div>
            <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
              <div class="text-xs text-gray-500">未缴罚金</div>
              <div
                class="text-xl font-semibold tracking-tight mt-1"
                :class="Number(profile.unpaid_fines) > 0 ? 'text-red-600' : 'text-gray-900'"
              >
                ¥{{ Number(profile.unpaid_fines || 0).toFixed(2) }}
              </div>
            </div>
          </div>
          <p class="text-sm text-gray-600 mt-3">累计发表书评 {{ profile.review_count }} 篇</p>
        </section>

        <section class="pt-5 border-t border-gray-200">
          <h3 class="text-base font-medium text-gray-900 mb-3">偏好分类 Top5</h3>
          <div v-if="favoriteCategories.length" class="space-y-3">
            <div v-for="category in favoriteCategories" :key="category.name">
              <div class="flex items-center justify-between text-sm">
                <span class="font-medium text-gray-700">{{ category.name }}</span>
                <span class="text-gray-500">{{ category.count }} 次</span>
              </div>
              <div class="mt-1.5 h-2 w-full rounded-full bg-gray-100">
                <div
                  class="h-2 rounded-full bg-blue-600 transition-colors duration-200"
                  :style="{ width: `${category.percent}%` }"
                ></div>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-600">暂无借阅偏好数据</p>
        </section>

        <section class="pt-5 border-t border-gray-200">
          <h3 class="text-base font-medium text-gray-900 mb-3">在借明细</h3>
          <div v-if="currentBorrows.length" class="overflow-x-auto scrollbar-thin rounded-lg border border-gray-200">
            <table class="w-full">
              <thead class="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">书名</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">借出日期</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">应还日期</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="item in currentBorrows" :key="item.record_id" class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-3 text-sm font-medium text-gray-900 max-w-xs truncate">{{ item.title || '-' }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(item.borrow_date) }}</td>
                  <td
                    class="px-4 py-3 text-sm"
                    :class="item.status === 'overdue' ? 'text-red-600 font-medium' : 'text-gray-600'"
                  >
                    {{ formatDate(item.due_date) }}
                  </td>
                  <td class="px-4 py-3">
                    <Badge :variant="item.status === 'overdue' ? 'danger' : 'primary'" size="small">
                      {{ item.status === 'overdue' ? `逾期 ${item.overdue_days} 天` : '在借' }}
                    </Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="text-sm text-gray-600">该读者当前没有在借图书</p>
        </section>
      </div>

      <template #footer>
        <Button variant="outline" @click="showProfileDialog = false">关闭</Button>
      </template>
    </Dialog>

    <!-- 新增读者 -->
    <Dialog v-model="showCreateDialog" title="新增读者" max-width="lg" persistent>
      <div class="space-y-4">
        <Alert v-if="formError" variant="error" title="提交失败" :message="formError" />
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input v-model="createForm.username" label="用户名" placeholder="登录账号" required />
          <Input v-model="createForm.full_name" label="真实姓名" required />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input v-model="createForm.email" label="电子邮箱" type="email" required />
          <Input v-model="createForm.phone" label="联系电话" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input v-model="createForm.password" label="初始密码" type="password" required />
          <Input v-model="createForm.card_number" label="借书卡号" hint="留空由系统自动生成" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select v-model="createForm.role" :options="roleOptions" label="角色" />
          <Input v-model.number="createForm.max_borrow_limit" type="number" label="可借册数" :min="1" />
        </div>
      </div>
      <template #footer>
        <Button variant="outline" @click="showCreateDialog = false">取消</Button>
        <Button variant="primary" :loading="submitting" @click="handleCreate">录入读者</Button>
      </template>
    </Dialog>

    <!-- 编辑读者 -->
    <Dialog v-model="showEditDialog" title="编辑读者信息" max-width="lg" persistent>
      <div class="space-y-4">
        <Alert v-if="formError" variant="error" title="保存失败" :message="formError" />
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input v-model="editForm.full_name" label="真实姓名" required />
          <Input v-model="editForm.email" label="电子邮箱" type="email" hint="邮箱变更由系统管理员复核" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input v-model="editForm.phone" label="联系电话" />
          <Input v-model.number="editForm.max_borrow_limit" type="number" label="可借册数" :min="1" />
        </div>
        <Select v-model="editForm.status" :options="statusEditOptions" label="账号状态" />
      </div>
      <template #footer>
        <Button variant="outline" @click="showEditDialog = false">取消</Button>
        <Button variant="primary" :loading="submitting" @click="handleUpdate">保存修改</Button>
      </template>
    </Dialog>

    <!-- 重置密码 -->
    <Dialog v-model="showResetDialog" title="重置读者密码" max-width="md" persistent>
      <p class="text-sm text-gray-600">
        确认将读者
        <span class="font-medium text-gray-900">{{ resetTarget?.full_name }}</span>
        （卡号 <span class="font-mono">{{ resetTarget?.card_number }}</span>）的密码重置为系统默认密码？重置后请提醒读者尽快修改。
      </p>
      <template #footer>
        <Button variant="outline" @click="showResetDialog = false">取消</Button>
        <Button variant="primary" :loading="submitting" @click="handleResetPassword">确认重置</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  ArrowPathIcon,
  BookOpenIcon,
  MagnifyingGlassIcon,
  NoSymbolIcon,
  UserPlusIcon,
  UsersIcon
} from '@heroicons/vue/24/outline'
import { useUserStore } from '@/stores/user'
import { borrowsApi, readersApi, statsApi } from '@/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Alert from '@/components/ui/Alert.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const userStore = useUserStore()

const readers = ref([])
const overview = ref({})
const activeReaderCount = ref(0)
const disabledCount = ref(0)
const loading = ref(false)
const submitting = ref(false)

const search = ref('')
const statusFilter = ref(null)
const roleFilter = ref(null)

const showProfileDialog = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showResetDialog = ref(false)

const profile = ref(null)
const profileLoading = ref(false)
const borrowDateMap = ref({})
const editTarget = ref(null)
const resetTarget = ref(null)
const formError = ref('')

const createForm = reactive({
  username: '',
  full_name: '',
  email: '',
  phone: '',
  password: '',
  card_number: '',
  role: 'reader',
  max_borrow_limit: 5
})

const editForm = reactive({
  full_name: '',
  email: '',
  phone: '',
  max_borrow_limit: 5,
  status: 'active'
})

const STATUS_MAP = {
  active: { label: '正常', variant: 'success' },
  frozen: { label: '已冻结', variant: 'danger' },
  suspended: { label: '已停用', variant: 'danger' },
  inactive: { label: '已停用', variant: 'danger' },
  expired: { label: '已过期', variant: 'warning' }
}

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '正常', value: 'active' },
  { label: '已冻结', value: 'frozen' }
]

const statusEditOptions = [
  { label: '正常', value: 'active' },
  { label: '已冻结', value: 'frozen' }
]

const roleOptions = [
  { label: '读者', value: 'reader' },
  { label: '馆员', value: 'librarian' },
  { label: '管理员', value: 'admin' }
]

const ROLE_LABELS = { admin: '管理员', librarian: '馆员', reader: '读者' }

const statusLabel = (status) => STATUS_MAP[status]?.label || status || '-'
const statusVariant = (status) => STATUS_MAP[status]?.variant || 'default'
const roleLabel = (role) => ROLE_LABELS[role] || role
const formatDate = (value) => (value ? new Date(value).toLocaleDateString('zh-CN') : '-')
const formatMoney = (value) => `¥${Number(value || 0).toFixed(2)}`

const profileBasic = computed(() => {
  const user = profile.value?.user
  if (!user) return []
  return [
    { label: '姓名', value: user.full_name || '-' },
    { label: '用户名', value: user.username || '-' },
    { label: '借书卡号', value: user.card_number || '-', mono: true },
    { label: '邮箱', value: user.email || '-' },
    { label: '电话', value: user.phone || '-' },
    { label: '角色', value: roleLabel(user.role) },
    { label: '账号状态', value: statusLabel(user.status) },
    { label: '可借册数', value: `${user.max_borrow_limit} 册` },
    { label: '账户余额', value: formatMoney(user.balance) },
    { label: '注册时间', value: formatDate(user.created_at) }
  ]
})

// 偏好分类按最高次数换算成百分比，用于横向条形展示
const favoriteCategories = computed(() => {
  const list = profile.value?.favorite_categories || []
  const max = Math.max(...list.map((item) => item.count), 0)
  return list.map((item) => ({
    ...item,
    percent: max > 0 ? Math.round((item.count / max) * 100) : 0
  }))
})

const currentBorrows = computed(() => {
  const list = profile.value?.current_borrows || []
  return list.map((item) => ({
    ...item,
    borrow_date: borrowDateMap.value[item.record_id] || null
  }))
})

async function loadOverview() {
  try {
    const [{ data: stats }, { data: actives }, { data: frozen }] = await Promise.all([
      statsApi.getOverview(),
      statsApi.getActiveReaders(100),
      // 停用人数独立统计，避免受列表筛选条件影响
      readersApi.getList({ status_filter: 'frozen', limit: 100 })
    ])
    overview.value = stats
    activeReaderCount.value = actives.filter((item) => (item.active_borrows || 0) > 0).length
    disabledCount.value = frozen.length
  } catch (err) {
    window.$toast?.error('加载读者统计失败')
  }
}

async function loadReaders() {
  loading.value = true
  try {
    const { data } = await readersApi.getList({
      search: search.value || undefined,
      status_filter: statusFilter.value || undefined,
      role_filter: roleFilter.value || undefined
    })
    readers.value = data
  } catch (err) {
    window.$toast?.error('加载读者列表失败')
  } finally {
    loading.value = false
  }
}

async function openProfile(reader) {
  showProfileDialog.value = true
  profileLoading.value = true
  profile.value = null
  borrowDateMap.value = {}
  try {
    const { data } = await readersApi.getOverview(reader.id)
    profile.value = data
    // 画像接口未返回借出日期，按读者补查借阅流水以完整展示在借明细
    try {
      const { data: records } = await borrowsApi.getList({ user_id: reader.id, limit: 100 })
      borrowDateMap.value = records.reduce((map, record) => {
        map[record.id] = record.borrow_date
        return map
      }, {})
    } catch (err) {
      borrowDateMap.value = {}
    }
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '加载读者画像失败')
    showProfileDialog.value = false
  } finally {
    profileLoading.value = false
  }
}

function openCreate() {
  formError.value = ''
  Object.assign(createForm, {
    username: '',
    full_name: '',
    email: '',
    phone: '',
    password: '',
    card_number: '',
    role: 'reader',
    max_borrow_limit: 5
  })
  showCreateDialog.value = true
}

async function handleCreate() {
  formError.value = ''
  if (!createForm.username || !createForm.full_name || !createForm.email || !createForm.password) {
    formError.value = '用户名、姓名、邮箱与初始密码为必填项'
    return
  }

  submitting.value = true
  try {
    const payload = { ...createForm, card_number: createForm.card_number || null }
    await readersApi.create(payload)
    window.$toast?.success('读者已录入，借书卡同步发放')
    showCreateDialog.value = false
    loadReaders()
    loadOverview()
  } catch (err) {
    formError.value = err.response?.data?.detail || '录入读者失败'
  } finally {
    submitting.value = false
  }
}

function openEdit(reader) {
  formError.value = ''
  editTarget.value = reader
  Object.assign(editForm, {
    full_name: reader.full_name || '',
    email: reader.email || '',
    phone: reader.phone || '',
    max_borrow_limit: reader.max_borrow_limit ?? 5,
    status: reader.status || 'active'
  })
  showEditDialog.value = true
}

async function handleUpdate() {
  formError.value = ''
  if (!editForm.full_name) {
    formError.value = '真实姓名不能为空'
    return
  }

  submitting.value = true
  try {
    await readersApi.update(editTarget.value.id, {
      full_name: editForm.full_name,
      email: editForm.email || undefined,
      phone: editForm.phone || '',
      max_borrow_limit: editForm.max_borrow_limit,
      status: editForm.status
    })
    window.$toast?.success('读者信息已更新')
    showEditDialog.value = false
    loadReaders()
  } catch (err) {
    formError.value = err.response?.data?.detail || '保存读者信息失败'
  } finally {
    submitting.value = false
  }
}

function openResetPassword(reader) {
  resetTarget.value = reader
  showResetDialog.value = true
}

async function handleResetPassword() {
  submitting.value = true
  try {
    const { data } = await readersApi.resetPassword(resetTarget.value.id)
    window.$toast?.success(data?.message || '密码已重置为 123456')
    showResetDialog.value = false
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '重置密码失败')
  } finally {
    submitting.value = false
  }
}

// 关键词输入防抖，避免每次按键都请求后端
let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadReaders, 300)
})

watch([statusFilter, roleFilter], loadReaders)

onMounted(() => {
  loadReaders()
  loadOverview()
})
</script>
