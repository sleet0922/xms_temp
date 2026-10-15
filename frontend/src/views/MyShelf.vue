<template>
  <div class="neo-page">
    <PageHeader title="我的书架" subtitle="在借图书、借阅时间线、预约排队与我的书评">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadAll">刷新</Button>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        label="在借图书"
        :value="overview.user_borrowed || 0"
        hint="尚未归还的图书"
        :icon="BookOpenIcon"
        tone="primary"
      />
      <StatCard
        label="逾期未还"
        :value="overview.user_overdue || 0"
        hint="请尽快归还以免产生罚金"
        :icon="ExclamationCircleIcon"
        :tone="overview.user_overdue > 0 ? 'danger' : 'neutral'"
      />
      <StatCard
        label="预约中"
        :value="activeReservationCount"
        hint="等待与已到馆的预约"
        :icon="ClipboardDocumentListIcon"
        tone="warning"
      />
      <StatCard
        label="未缴罚金"
        :value="`¥${money(overview.user_fines)}`"
        hint="可在罚金中心缴纳"
        :icon="CurrencyYenIcon"
        :tone="Number(overview.user_fines) > 0 ? 'danger' : 'neutral'"
      />
    </div>

    <div v-if="loading" class="text-sm text-gray-500 mb-4">数据加载中…</div>

    <Tabs v-model="activeTab" :tabs="tabs">
      <!-- 在借图书 -->
      <template #panel-0>
        <div v-if="activeBorrows.length" class="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
          <Card v-for="record in activeBorrows" :key="record.id" padding="small" hover>
            <div class="flex gap-4">
              <button type="button" class="w-24 flex-shrink-0 focus:outline-none" @click="goBook(record.book?.id)">
                <BookCover :book="record.book || {}" ratio="3/4" />
              </button>
              <div class="min-w-0 flex-1 flex flex-col">
                <button type="button" class="text-left focus:outline-none" @click="goBook(record.book?.id)">
                  <h3 class="text-sm font-medium text-gray-900 line-clamp-2 hover:text-[#2f5b4e]">{{ record.book?.title || '-' }}</h3>
                </button>
                <p class="text-xs text-gray-500 truncate mt-1">{{ record.book?.author || '-' }}</p>
                <div class="mt-3 text-xs text-gray-500">应还 {{ formatDate(record.due_date) }}</div>
                <div class="mt-0.5 text-sm font-medium" :class="dueTextClass(record)">{{ dueText(record) }}</div>
                <div class="mt-auto pt-3 flex items-center justify-between gap-2">
                  <span class="text-xs text-gray-500">已续借 {{ record.renew_count || 0 }} 次</span>
                  <div class="flex items-center gap-2">
                    <Button
                      size="small"
                      variant="outline"
                      :loading="renewingId === record.id"
                      :disabled="record.renew_count >= systemStore.maxRenewTimes"
                      :title="record.renew_count >= systemStore.maxRenewTimes ? `已达最大续借次数（${systemStore.maxRenewTimes} 次）` : ''"
                      @click="renew(record)"
                    >
                      续借
                    </Button>
                    <Button
                      v-if="record.return_request_status !== 'pending'"
                      size="small"
                      variant="primary"
                      :loading="returnRequestId === record.id"
                      @click="requestReturn(record)"
                    >
                      提前还书
                    </Button>
                    <span v-else class="text-xs text-amber-700">待确认</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
        <EmptyState
          v-if="!loading && !activeBorrows.length"
          title="当前没有在借图书"
          description="去馆藏检索挑一本喜欢的书吧"
          :icon="BookOpenIcon"
        />
      </template>

      <!-- 借阅时间线 -->
      <template #panel-1>
        <Card v-if="timeline.length">
          <div class="relative border-l-2 border-gray-200 ml-3 space-y-6">
            <div v-for="record in timeline" :key="record.id" class="relative pl-6">
              <span class="absolute -left-[7px] top-1.5 w-3 h-3 rounded-full" :class="nodeClass(record)"></span>
              <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                <button
                  type="button"
                  class="text-left text-sm font-medium text-gray-900 hover:text-blue-700 rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  @click="goBook(record.book?.id)"
                >
                  {{ record.book?.title || '-' }}
                </button>
                <span class="text-xs text-gray-500">借出 {{ formatDate(record.borrow_date) }}</span>
              </div>
              <div class="text-xs text-gray-600 mt-1">
                归还：{{ record.return_date ? formatDate(record.return_date) : '未归还' }}
                <span v-if="overdueDays(record) > 0" class="text-red-600 ml-2">逾期 {{ overdueDays(record) }} 天</span>
              </div>
            </div>
          </div>
        </Card>
        <EmptyState
          v-if="!loading && !timeline.length"
          title="暂无借阅记录"
          description="借阅成功后会在这里形成时间线"
          :icon="ClockIcon"
        />
      </template>

      <!-- 我的预约 -->
      <template #panel-2>
        <Card v-if="reservations.length" padding="none">
          <div class="overflow-x-auto scrollbar-thin">
            <table class="w-full">
              <thead class="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">图书</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">预约日期</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">到期日期</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="reservation in reservations" :key="reservation.id" class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-3 text-sm">
                    <button
                      type="button"
                      class="text-left font-medium text-gray-900 hover:text-blue-700 rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      @click="goBook(reservation.book?.id)"
                    >
                      {{ reservation.book?.title || '-' }}
                    </button>
                    <div class="text-xs text-gray-500">{{ reservation.book?.author || '-' }}</div>
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(reservation.reserve_date) }}</td>
                  <td class="px-4 py-3 text-sm" :class="isExpiring(reservation) ? 'text-amber-700 font-medium' : 'text-gray-600'">
                    {{ formatDate(reservation.expire_date) }}
                  </td>
                  <td class="px-4 py-3">
                    <Badge :variant="reservationVariant(reservation.status)" size="small">
                      {{ reservationLabel(reservation.status) }}
                    </Badge>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <Button
                      v-if="isActiveReservation(reservation.status)"
                      size="small"
                      variant="outline"
                      @click="cancelReservation(reservation)"
                    >
                      取消
                    </Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
        <EmptyState
          v-if="!loading && !reservations.length"
          title="暂无预约记录"
          description="缺货图书可在图书详情页发起预约"
          :icon="ClipboardDocumentListIcon"
        />
      </template>

      <!-- 我的书评 -->
      <template #panel-3>
        <Card v-if="reviews.length">
          <div class="divide-y divide-gray-200">
            <div v-for="review in reviews" :key="review.id" class="py-4 first:pt-0 last:pb-0">
              <div class="flex items-start justify-between gap-4">
                <div class="min-w-0">
                  <button
                    type="button"
                    class="text-left text-sm font-medium text-gray-900 hover:text-blue-700 rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    @click="goBook(review.book?.id)"
                  >
                    {{ review.book?.title || '-' }}
                  </button>
                  <div class="mt-1">
                    <RatingStars :model-value="review.rating" size="small" />
                  </div>
                </div>
                <Button size="small" variant="danger" @click="removeReview(review)">删除</Button>
              </div>
              <p v-if="review.content" class="text-sm text-gray-600 mt-2">{{ review.content }}</p>
              <p class="text-xs text-gray-500 mt-2">更新于 {{ formatDate(review.updated_at) }}</p>
            </div>
          </div>
        </Card>
        <EmptyState
          v-if="!loading && !reviews.length"
          title="还没有写过书评"
          description="在图书详情页为读过的书写下感受"
          :icon="ChatBubbleLeftRightIcon"
        />
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowPathIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  CurrencyYenIcon,
  ExclamationCircleIcon
} from '@heroicons/vue/24/outline'
import { borrowsApi, reservationsApi, reviewsApi, statsApi } from '@/api'
import { useSystemStore } from '@/stores/system'
import {
  isActiveReservation,
  reservationStatusLabel,
  reservationStatusVariant
} from '@/utils/labels'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Tabs from '@/components/ui/Tabs.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import BookCover from '@/components/ui/BookCover.vue'
import RatingStars from '@/components/ui/RatingStars.vue'

const router = useRouter()
const systemStore = useSystemStore()

const tabs = ['在借图书', '借阅时间线', '我的预约', '我的书评']
const activeTab = ref(0)

const overview = ref({})
const borrows = ref([])
const reservations = ref([])
const reviews = ref([])
const loading = ref(false)
const renewingId = ref(null)
const returnRequestId = ref(null)

const activeBorrows = computed(() => borrows.value.filter(r => !r.return_date))
// overview 的 total_reservations 是全馆口径，此处按列表（读者视角已按本人过滤）统计个人预约中数量
const activeReservationCount = computed(
  () => reservations.value.filter(r => ['waiting', 'notified'].includes(r.status)).length
)
const timeline = computed(() =>
  [...borrows.value].sort((a, b) => new Date(b.borrow_date) - new Date(a.borrow_date))
)

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN')
}

const money = (value) => Number(value || 0).toFixed(2)

const daysLeft = (dueDate) => {
  if (!dueDate) return null
  return Math.ceil((new Date(dueDate) - Date.now()) / 86400000)
}

const dueText = (record) => {
  const days = daysLeft(record.due_date)
  if (days === null) return '应还日期未知'
  if (days < 0) return `已逾期 ${Math.abs(days)} 天`
  if (days === 0) return '今天到期'
  return `剩余 ${days} 天`
}

const dueTextClass = (record) => {
  const days = daysLeft(record.due_date)
  if (days === null) return 'text-gray-500'
  if (days < 0) return 'text-red-600'
  if (days <= 3) return 'text-amber-700'
  return 'text-gray-600'
}

// 后端已回填 overdue_days；字段缺失时按应还日期兜底计算
const overdueDays = (record) => {
  if (record.return_date) return 0
  const days = daysLeft(record.due_date)
  if (days === null || days >= 0) return 0
  return record.overdue_days > 0 ? record.overdue_days : Math.abs(days)
}

const nodeClass = (record) => {
  if (record.return_date) return 'bg-green-600'
  if (overdueDays(record) > 0 || record.status === 'overdue') return 'bg-red-600'
  return 'bg-blue-600'
}

const isExpiring = (reservation) => {
  if (reservation.status !== 'waiting' && reservation.status !== 'notified') return false
  const days = daysLeft(reservation.expire_date)
  return days !== null && days <= 3
}

const reservationLabel = reservationStatusLabel
const reservationVariant = reservationStatusVariant

const goBook = (bookId) => {
  if (bookId) router.push(`/books/${bookId}`)
}

// 各区块独立容错，单个接口失败不影响其他面板
async function loadAll() {
  loading.value = true
  const [overviewRes, borrowsRes, reservationsRes, reviewsRes] = await Promise.all([
    statsApi.getOverview().then(r => r.data).catch(() => null),
    borrowsApi.getMyBorrows().then(r => r.data).catch(() => null),
    reservationsApi.getList().then(r => r.data).catch(() => null),
    reviewsApi.getMine().then(r => r.data).catch(() => null)
  ])

  if (overviewRes) overview.value = overviewRes
  else window.$toast?.error('概览指标加载失败')

  if (borrowsRes) borrows.value = borrowsRes
  else window.$toast?.error('借阅记录加载失败')

  if (reservationsRes) reservations.value = reservationsRes
  else window.$toast?.error('预约记录加载失败')

  if (reviewsRes) reviews.value = reviewsRes
  else window.$toast?.error('书评加载失败')

  loading.value = false
}

async function renew(record) {
  renewingId.value = record.id
  try {
    await borrowsApi.renewBorrow(record.id)
    window.$toast?.success('续借成功')
    await loadAll()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '续借失败')
  } finally {
    renewingId.value = null
  }
}

async function requestReturn(record) {
  if (!window.confirm(`确认申请提前归还《${record.book?.title || '这本书'}》吗？提交后请将图书交给管理员确认。`)) return
  returnRequestId.value = record.id
  try {
    await borrowsApi.requestReturn(record.id)
    window.$toast?.success('还书申请已提交，请将图书交给管理员确认')
    await loadAll()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '提交还书申请失败')
  } finally {
    returnRequestId.value = null
  }
}

async function cancelReservation(reservation) {
  if (!window.confirm(`确认取消对《${reservation.book?.title || '该图书'}》的预约？`)) return
  try {
    await reservationsApi.cancel(reservation.id)
    window.$toast?.success('已取消预约')
    await loadAll()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '取消失败')
  }
}

async function removeReview(review) {
  if (!window.confirm(`确认删除对《${review.book?.title || '该图书'}》的书评？`)) return
  try {
    await reviewsApi.remove(review.id)
    window.$toast?.success('书评已删除')
    await loadAll()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '删除失败')
  }
}

onMounted(loadAll)
</script>
