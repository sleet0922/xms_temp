<template>
  <div class="neo-page">
    <PageHeader :title="canManage ? '借阅记录' : '借阅中心'" :subtitle="canManage ? '全馆借阅、逾期与续借记录' : '查看我的在借、逾期与历史借阅记录'">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadBorrows">刷新</Button>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        v-for="card in statCards"
        :key="card.label"
        :label="card.label"
        :value="card.value"
        :hint="card.hint"
        :icon="card.icon"
        :tone="card.tone"
      />
    </div>

    <!-- 筛选区 -->
    <Card class="mb-6">
      <Tabs v-model="activeStatus" :tabs="statusTabs" />
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          v-model="searchInput"
          label="关键词"
          placeholder="书名、ISBN"
          :prepend-icon="MagnifyingGlassIcon"
        />
        <Select
          v-if="canManage"
          v-model="readerId"
          :options="readerOptions"
          label="读者"
          placeholder="全部读者"
          item-title="label"
          item-value="value"
        />
      </div>
    </Card>

    <!-- 借阅流水 -->
    <Card padding="none">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">图书</th>
              <th v-if="canManage" class="px-4 py-3 text-left text-xs font-semibold text-gray-600">读者</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">借出日期</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">应还日期</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">归还日期</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
              <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-if="loading">
              <td :colspan="columnCount" class="px-4 py-3 text-sm text-gray-500">借阅记录加载中…</td>
            </tr>
            <tr v-for="record in records" :key="record.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 text-sm">
                <button
                  type="button"
                  class="text-left font-medium text-gray-900 hover:text-blue-700 rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  @click="goBook(record.book?.id)"
                >
                  {{ record.book?.title || '-' }}
                </button>
                <div class="text-xs text-gray-500">{{ record.book?.author || '-' }}</div>
              </td>
              <td v-if="canManage" class="px-4 py-3 text-sm text-gray-600">
                {{ record.user?.full_name || '-' }}
                <div class="text-xs text-gray-500">{{ record.user?.card_number || '-' }}</div>
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(record.borrow_date) }}</td>
              <td class="px-4 py-3 text-sm" :class="isOverdue(record) ? 'text-red-600 font-medium' : 'text-gray-600'">
                {{ formatDate(record.due_date) }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ record.return_date ? formatDate(record.return_date) : '-' }}</td>
              <td class="px-4 py-3">
                <Badge :variant="statusVariant(record)" size="small">{{ statusLabel(record) }}</Badge>
                <div v-if="overdueDays(record) > 0" class="text-xs text-red-600 mt-1">
                  逾期 {{ overdueDays(record) }} 天
                  <span v-if="Number(record.calculated_fine) > 0">· 罚金 ¥{{ money(record.calculated_fine) }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-right">
                <Button
                  v-if="!record.return_date"
                  size="small"
                  variant="outline"
                  :loading="renewingId === record.id"
                  :disabled="record.renew_count >= systemStore.maxRenewTimes"
                  :title="record.renew_count >= systemStore.maxRenewTimes ? `已达最大续借次数（${systemStore.maxRenewTimes} 次）` : ''"
                  @click="renew(record)"
                >
                  续借
                </Button>
                <span v-if="!record.return_date && record.renew_count > 0" class="text-xs text-gray-500 ml-2">已续借 {{ record.renew_count }} 次</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState
        v-if="!loading && !records.length"
        title="暂无借阅记录"
        description="换个状态筛选或关键词再试试"
        :icon="BookOpenIcon"
      />
    </Card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ArrowUpTrayIcon,
  BookOpenIcon,
  ExclamationCircleIcon,
  MagnifyingGlassIcon
} from '@heroicons/vue/24/outline'
import { useUserStore } from '@/stores/user'
import { useSystemStore } from '@/stores/system'
import { borrowsApi, readersApi, statsApi } from '@/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Tabs from '@/components/ui/Tabs.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Badge from '@/components/ui/Badge.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const systemStore = useSystemStore()
const canManage = computed(() => route.path.startsWith('/admin') && userStore.isLibrarian)

const statusTabs = ['全部', '在借', '逾期', '已还']
// Tabs 索引与后端 status_filter 的映射
const STATUS_VALUES = [undefined, 'borrowed', 'overdue', 'returned']

const records = ref([])
const stats = ref({})
const readers = ref([])
const activeStatus = ref(0)
const searchInput = ref('')
const search = ref('')
const readerId = ref(null)
const loading = ref(false)
const renewingId = ref(null)

const columnCount = computed(() => (canManage.value ? 7 : 6))

// 0 表示不限定读者（user_id 为 0 时按未筛选处理）
const readerOptions = computed(() => [
  { label: '全部读者', value: 0 },
  ...readers.value.map(r => ({ label: `${r.full_name}（${r.card_number || r.username}）`, value: r.id }))
])

const statCards = computed(() => {
  const s = stats.value
  if (!canManage.value) {
    return [
      { label: '我的在借', value: s.user_borrowed || 0, hint: '尚未归还的图书', icon: BookOpenIcon, tone: 'primary' },
      { label: '我的逾期', value: s.user_overdue || 0, hint: '请尽快归还以免产生罚金', icon: ExclamationCircleIcon, tone: 'danger' },
      { label: '今日借出', value: s.today_borrows || 0, hint: '全馆今日借出量', icon: ArrowUpTrayIcon, tone: 'neutral' },
      { label: '今日归还', value: s.today_returns || 0, hint: '全馆今日归还量', icon: ArrowDownTrayIcon, tone: 'neutral' }
    ]
  }
  return [
    { label: '在借总数', value: s.active_borrows || 0, hint: '全馆未归还记录', icon: BookOpenIcon, tone: 'primary' },
    { label: '逾期数', value: s.overdue_borrows || 0, hint: '需要催还的记录', icon: ExclamationCircleIcon, tone: 'danger' },
    { label: '今日借出', value: s.today_borrows || 0, hint: '今日新借出', icon: ArrowUpTrayIcon, tone: 'success' },
    { label: '今日归还', value: s.today_returns || 0, hint: '今日已归还', icon: ArrowDownTrayIcon, tone: 'neutral' }
  ]
})

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN')
}

const money = (value) => Number(value || 0).toFixed(2)

// 后端已回填 overdue_days；字段缺失时按应还日期兜底计算
const isOverdue = (record) => {
  if (record.return_date) return false
  if (record.status === 'overdue') return true
  return !!record.due_date && new Date(record.due_date) < new Date()
}

const overdueDays = (record) => {
  if (!isOverdue(record) || !record.due_date) return 0
  if (record.overdue_days > 0) return record.overdue_days
  return Math.max(1, Math.floor((Date.now() - new Date(record.due_date)) / 86400000))
}

const statusLabel = (record) => {
  if (record.status === 'returned') return '已还'
  if (isOverdue(record)) return '逾期'
  const labels = { borrowed: '在借', lost: '遗失' }
  return labels[record.status] || record.status
}

const statusVariant = (record) => {
  if (record.status === 'returned') return 'success'
  if (isOverdue(record)) return 'danger'
  if (record.status === 'lost') return 'warning'
  return 'primary'
}

const goBook = (bookId) => {
  if (bookId) router.push(`${canManage.value ? '/admin/books' : '/books'}/${bookId}`)
}

async function loadBorrows() {
  loading.value = true
  try {
    const { data } = await borrowsApi.getList({
      status_filter: STATUS_VALUES[activeStatus.value],
      search: search.value || undefined,
      user_id: readerId.value || undefined,
      limit: 100
    })
    records.value = data
  } catch (err) {
    window.$toast?.error('加载借阅记录失败')
  } finally {
    loading.value = false
  }
}

async function loadOverview() {
  try {
    const { data } = await statsApi.getOverview()
    stats.value = data
  } catch (err) {
    console.error('加载概览指标失败', err)
  }
}

async function loadReaders() {
  if (!canManage.value) return
  try {
    const { data } = await readersApi.getList({ role_filter: 'reader', limit: 100 })
    readers.value = data
  } catch (err) {
    console.error('加载读者列表失败', err)
  }
}

async function renew(record) {
  renewingId.value = record.id
  try {
    await borrowsApi.renewBorrow(record.id)
    window.$toast?.success('续借成功')
    await Promise.all([loadBorrows(), loadOverview()])
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '续借失败')
  } finally {
    renewingId.value = null
  }
}

// 关键词输入防抖 300ms
let searchTimer = null
watch(searchInput, (value) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    search.value = value.trim()
  }, 300)
})

watch([activeStatus, search, readerId], loadBorrows)

onMounted(() => {
  loadBorrows()
  loadOverview()
  loadReaders()
})
</script>
