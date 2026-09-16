<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">预约排队</h1>
        <p class="text-gray-600 mt-1">图书预约与到馆通知</p>
      </div>

      <Card padding="none">
        <div class="overflow-x-auto">
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
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ reservation.book?.title }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(reservation.reserve_date) }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(reservation.expire_date) }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="getStatusVariant(reservation.status)" size="small">
                    {{ getStatusLabel(reservation.status) }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right">
                  <Button
                    v-if="reservation.status === 'waiting'"
                    size="small"
                    variant="outline"
                    @click="cancelReservation(reservation.id)"
                  >
                    取消
                  </Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import { reservationsApi } from '@/api'

const reservations = ref([])

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const getStatusLabel = (status) => {
  const labels = { waiting: '等待中', notified: '已到馆', fulfilled: '已兑现', cancelled: '已取消' }
  return labels[status] || status
}

const getStatusVariant = (status) => {
  const variants = { waiting: 'warning', notified: 'primary', fulfilled: 'success', cancelled: 'default' }
  return variants[status] || 'default'
}

const loadReservations = async () => {
  try {
    const response = await reservationsApi.getList()
    reservations.value = response.data
  } catch (err) {
    window.$toast?.error('加载预约记录失败')
  }
}

const cancelReservation = async (id) => {
  if (!confirm('确认取消预约？')) return
  try {
    await reservationsApi.cancel(id)
    window.$toast?.success('已取消预约')
    loadReservations()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '取消失败')
  }
}

onMounted(() => {
  loadReservations()
})
</script>
