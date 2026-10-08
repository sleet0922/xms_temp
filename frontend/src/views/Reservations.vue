<template>
  <div class="neo-page p-6 lg:p-8 max-w-7xl mx-auto">
    <PageHeader title="预约排队" subtitle="缺货图书的预约队列与到馆提醒">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadReservations">刷新</Button>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
      <StatCard label="等待中" :value="summary.waiting" hint="排队等待图书到馆" :icon="ClockIcon" tone="warning" />
      <StatCard label="已到馆" :value="summary.notified" hint="请尽快到馆取书" :icon="BellAlertIcon" tone="primary" />
      <StatCard label="即将过期" :value="summary.expiring" hint="到期日在 3 天以内" :icon="ExclamationCircleIcon" tone="danger" />
    </div>

    <Card padding="none">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">图书</th>
              <th v-if="userStore.isLibrarian" class="px-4 py-3 text-left text-xs font-semibold text-gray-600">读者</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">预约日期</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">到期日期</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
              <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-if="loading">
              <td :colspan="columnCount" class="px-4 py-3 text-sm text-gray-500">预约记录加载中…</td>
            </tr>
            <tr v-for="reservation in reservations" :key="reservation.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 text-sm">
                <button
                  class="text-left font-medium text-gray-900 hover:text-blue-700 rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  @click="goBook(reservation.book?.id)"
                >
                  {{ reservation.book?.title || '-' }}
                </button>
                <div class="text-xs text-gray-500">{{ reservation.book?.author || '-' }}</div>
              </td>
              <td v-if="userStore.isLibrarian" class="px-4 py-3 text-sm text-gray-600">
                {{ reservation.user?.full_name || '-' }}
                <div class="text-xs text-gray-500">{{ reservation.user?.card_number || '-' }}</div>
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(reservation.reserve_date) }}</td>
              <td class="px-4 py-3 text-sm" :class="expireClass(reservation)">
                {{ formatDate(reservation.expire_date) }}
                <div v-if="expireHint(reservation)" class="text-xs">{{ expireHint(reservation) }}</div>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="statusVariant(reservation.status)" size="small">
                  {{ statusLabel(reservation.status) }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right">
                <Button
                  v-if="reservation.status === 'waiting'"
                  size="small"
                  variant="outline"
                  @click="openCancelDialog(reservation)"
                >
                  取消
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState
        v-if="!loading && !reservations.length"
        title="暂无预约记录"
        description="缺货图书可在图书详情页发起预约"
        :icon="ClipboardDocumentListIcon"
      />
    </Card>

    <!-- 取消预约二次确认 -->
    <Dialog v-model="showCancelDialog" title="取消预约" max-width="sm">
      <p class="text-sm text-gray-600">
        确认取消对《{{ cancelTarget?.book?.title || '该图书' }}》的预约？取消后需要重新排队。
      </p>
      <template #footer>
        <Button variant="outline" @click="showCancelDialog = false">再想想</Button>
        <Button variant="danger" :loading="cancelling" @click="confirmCancel">确认取消</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowPathIcon,
  BellAlertIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  ExclamationCircleIcon
} from '@heroicons/vue/24/outline'
import { useUserStore } from '@/stores/user'
import { reservationsApi } from '@/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const router = useRouter()
const userStore = useUserStore()

const reservations = ref([])
const loading = ref(false)
const cancelling = ref(false)
const showCancelDialog = ref(false)
const cancelTarget = ref(null)

const columnCount = computed(() => (userStore.isLibrarian ? 6 : 5))

const summary = computed(() => {
  const active = reservations.value.filter(r => ['waiting', 'notified'].includes(r.status))
  return {
    waiting: reservations.value.filter(r => r.status === 'waiting').length,
    notified: reservations.value.filter(r => r.status === 'notified').length,
    expiring: active.filter(r => {
      const days = daysLeft(r.expire_date)
      return days !== null && days >= 0 && days <= 3
    }).length
  }
})

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN')
}

const daysLeft = (dateStr) => {
  if (!dateStr) return null
  return Math.ceil((new Date(dateStr) - Date.now()) / 86400000)
}

const isActive = (reservation) => ['waiting', 'notified'].includes(reservation.status)

const expireClass = (reservation) => {
  if (!isActive(reservation)) return 'text-gray-600'
  const days = daysLeft(reservation.expire_date)
  if (days === null) return 'text-gray-600'
  if (days < 0) return 'text-red-600 font-medium'
  if (days <= 3) return 'text-amber-600 font-medium'
  return 'text-gray-600'
}

const expireHint = (reservation) => {
  if (!isActive(reservation)) return ''
  const days = daysLeft(reservation.expire_date)
  if (days === null) return ''
  if (days < 0) return `已过期 ${Math.abs(days)} 天`
  if (days <= 3) return `仅剩 ${days} 天`
  return ''
}

const statusLabel = (status) => {
  const labels = { waiting: '等待中', notified: '已到馆', fulfilled: '已兑现', cancelled: '已取消' }
  return labels[status] || status
}

const statusVariant = (status) => {
  const variants = { waiting: 'warning', notified: 'primary', fulfilled: 'success', cancelled: 'default' }
  return variants[status] || 'default'
}

const goBook = (bookId) => {
  if (bookId) router.push(`/books/${bookId}`)
}

async function loadReservations() {
  loading.value = true
  try {
    const { data } = await reservationsApi.getList()
    reservations.value = data
  } catch (err) {
    window.$toast?.error('加载预约记录失败')
  } finally {
    loading.value = false
  }
}

function openCancelDialog(reservation) {
  cancelTarget.value = reservation
  showCancelDialog.value = true
}

async function confirmCancel() {
  if (!cancelTarget.value) return
  cancelling.value = true
  try {
    await reservationsApi.cancel(cancelTarget.value.id)
    window.$toast?.success('已取消预约')
    showCancelDialog.value = false
    cancelTarget.value = null
    await loadReservations()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '取消失败')
  } finally {
    cancelling.value = false
  }
}

onMounted(loadReservations)
</script>
