<template>
  <div class="neo-page">
    <PageHeader :title="canManage ? '预约管理' : '预约排队'" :subtitle="canManage ? '查看队列并为到馆读者办理借出' : '缺货图书的预约队列与到馆提醒'">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadReservations">刷新</Button>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
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
              <th v-if="canManage" class="px-4 py-3 text-left text-xs font-semibold text-gray-600">读者</th>
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
                  type="button"
                  class="text-left font-medium text-gray-900 hover:text-blue-700 rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  @click="goBook(reservation.book?.id)"
                >
                  {{ reservation.book?.title || '-' }}
                </button>
                <div class="text-xs text-gray-500">{{ reservation.book?.author || '-' }}</div>
              </td>
              <td v-if="canManage" class="px-4 py-3 text-sm text-gray-600">
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
                <div class="flex items-center justify-end gap-2">
                  <!-- 读者端：取书需在服务台由馆员办理，这里给出明确指引 -->
                  <span
                    v-if="!canManage && reservation.status === 'notified'"
                    class="text-xs font-medium text-[#2f5b4e]"
                  >
                    请到服务台取书
                  </span>
                  <Button
                    v-if="canFulfill(reservation)"
                    size="small"
                    variant="primary"
                    :loading="fulfillingId === reservation.id"
                    @click="openFulfillDialog(reservation)"
                  >
                    办理借出
                  </Button>
                  <Button
                    v-if="canCancel(reservation)"
                    size="small"
                    variant="outline"
                    :loading="cancellingId === reservation.id"
                    @click="openCancelDialog(reservation)"
                  >
                    取消
                  </Button>
                  <span v-if="!canCancel(reservation) && !canFulfill(reservation)" class="text-xs text-gray-500">已结束</span>
                </div>
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

    <!-- 预约取书：为读者办理借出，闭环兑现预约 -->
    <Dialog v-model="showFulfillDialog" title="预约取书" max-width="sm">
      <p class="text-sm text-gray-600">
        确认为
        <span class="font-medium text-gray-900">{{ fulfillTarget?.user?.full_name || '该读者' }}</span>
        办理《{{ fulfillTarget?.book?.title || '该图书' }}》的借出？
        办理后将生成借阅记录，应还日期按系统借期自动计算。
      </p>
      <template #footer>
        <Button variant="outline" @click="showFulfillDialog = false">取消</Button>
        <Button variant="primary" :loading="fulfilling" @click="confirmFulfill">确认办理</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowPathIcon,
  BellAlertIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  ExclamationCircleIcon
} from '@heroicons/vue/24/outline'
import { useUserStore } from '@/stores/user'
import { reservationsApi } from '@/api'
import {
  isActiveReservation,
  reservationStatusLabel,
  reservationStatusVariant
} from '@/utils/labels'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const canManage = computed(() => route.path.startsWith('/admin') && userStore.isLibrarian)

const reservations = ref([])
const loading = ref(false)
const cancelling = ref(false)
const cancellingId = ref(null)
const showCancelDialog = ref(false)
const cancelTarget = ref(null)
const fulfilling = ref(false)
const fulfillingId = ref(null)
const showFulfillDialog = ref(false)
const fulfillTarget = ref(null)

const columnCount = computed(() => (canManage.value ? 6 : 5))

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

const isActive = (reservation) => isActiveReservation(reservation.status)

// 只要预约仍在进行且馆内有在架复本，馆员即可为读者办理取书
const canFulfill = (reservation) =>
  canManage.value &&
  isActiveReservation(reservation.status) &&
  (reservation.book?.available_copies ?? 0) > 0

// 「已到馆」预约同样允许取消（读者放弃取书），后端会顺延给队列下一位
const canCancel = (reservation) => isActiveReservation(reservation.status)

const expireClass = (reservation) => {
  if (!isActive(reservation)) return 'text-gray-600'
  const days = daysLeft(reservation.expire_date)
  if (days === null) return 'text-gray-600'
  if (days < 0) return 'text-red-600 font-medium'
  if (days <= 3) return 'text-amber-700 font-medium'
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

const statusLabel = reservationStatusLabel
const statusVariant = reservationStatusVariant

const goBook = (bookId) => {
  if (bookId) router.push(`${canManage.value ? '/admin/books' : '/books'}/${bookId}`)
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
  cancellingId.value = cancelTarget.value.id
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
    cancellingId.value = null
  }
}

function openFulfillDialog(reservation) {
  fulfillTarget.value = reservation
  showFulfillDialog.value = true
}

async function confirmFulfill() {
  if (!fulfillTarget.value) return
  fulfilling.value = true
  fulfillingId.value = fulfillTarget.value.id
  try {
    const { data } = await reservationsApi.fulfill(fulfillTarget.value.id)
    const due = data?.due_date ? new Date(data.due_date).toLocaleDateString('zh-CN') : ''
    window.$toast?.success(due ? `已办理借出，应还日期 ${due}` : '已办理借出')
    showFulfillDialog.value = false
    fulfillTarget.value = null
    await loadReservations()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '办理取书失败')
  } finally {
    fulfilling.value = false
    fulfillingId.value = null
  }
}

onMounted(loadReservations)
</script>
