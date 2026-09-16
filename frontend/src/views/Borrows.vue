<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">借阅流转中心</h1>
        <p class="text-gray-600 mt-1">在借图书与借阅记录查询</p>
      </div>

      <!-- Status Tabs -->
      <Card padding="none" class="mb-6">
        <div class="border-b border-gray-200">
          <div class="flex gap-4 px-6">
            <button
              v-for="status in statusFilters"
              :key="status.value"
              @click="activeStatus = status.value"
              :class="[
                'py-4 px-2 border-b-2 transition-colors text-sm font-medium',
                activeStatus === status.value
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              ]"
            >
              {{ status.label }}
              <Badge v-if="status.count !== undefined" :variant="status.variant" size="small" class="ml-2">
                {{ status.count }}
              </Badge>
            </button>
          </div>
        </div>

        <div class="p-6">
          <Input v-model="search" placeholder="搜索书名、读者" :prepend-icon="MagnifyingGlassIcon" />
        </div>
      </Card>

      <!-- Borrows Table -->
      <Card padding="none">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">书名</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">读者</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">借出日期</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">应还日期</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="borrow in borrows" :key="borrow.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ borrow.book?.title }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ borrow.user?.full_name }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(borrow.borrow_date) }}</td>
                <td class="px-4 py-3 text-sm" :class="isOverdue(borrow) ? 'text-red-600 font-medium' : 'text-gray-600'">
                  {{ formatDate(borrow.due_date) }}
                  <span v-if="isOverdue(borrow)" class="ml-1">(逾期{{ getOverdueDays(borrow) }}天)</span>
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="getStatusVariant(borrow.status)" size="small">
                    {{ getStatusLabel(borrow.status) }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right">
                  <Button
                    v-if="borrow.status === 'borrowed' || borrow.status === 'overdue'"
                    size="small"
                    variant="ghost"
                    @click="renewBorrow(borrow.id)"
                    :disabled="borrow.renew_count >= 2"
                  >
                    续借({{ borrow.renew_count }}/2)
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
import { ref, computed, onMounted, watch } from 'vue'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Badge from '@/components/ui/Badge.vue'
import { borrowsApi } from '@/api'

const borrows = ref([])
const search = ref('')
const activeStatus = ref('all')

const statusFilters = computed(() => [
  { label: '全部', value: 'all', count: borrows.value.length },
  { label: '在借', value: 'borrowed', count: borrows.value.filter(b => b.status === 'borrowed').length, variant: 'primary' },
  { label: '逾期', value: 'overdue', count: borrows.value.filter(b => b.status === 'overdue').length, variant: 'danger' },
  { label: '已还', value: 'returned', count: borrows.value.filter(b => b.status === 'returned').length, variant: 'success' }
])

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const isOverdue = (borrow) => {
  return borrow.status === 'overdue' || (borrow.due_date && new Date(borrow.due_date) < new Date() && !borrow.return_date)
}

const getOverdueDays = (borrow) => {
  if (!borrow.due_date) return 0
  const days = Math.floor((new Date() - new Date(borrow.due_date)) / (1000 * 60 * 60 * 24))
  return Math.max(0, days)
}

const getStatusLabel = (status) => {
  const labels = { borrowed: '在借', returned: '已还', overdue: '逾期', lost: '遗失' }
  return labels[status] || status
}

const getStatusVariant = (status) => {
  const variants = { borrowed: 'primary', returned: 'success', overdue: 'danger', lost: 'warning' }
  return variants[status] || 'default'
}

const loadBorrows = async () => {
  try {
    const params = {
      status_filter: activeStatus.value === 'all' ? null : activeStatus.value,
      search: search.value
    }
    const response = await borrowsApi.getList(params)
    borrows.value = response.data
  } catch (err) {
    window.$toast?.error('加载借阅记录失败')
  }
}

const renewBorrow = async (id) => {
  try {
    await borrowsApi.renewBorrow(id)
    window.$toast?.success('续借成功')
    loadBorrows()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '续借失败')
  }
}

watch([activeStatus, search], () => {
  loadBorrows()
})

onMounted(() => {
  loadBorrows()
})
</script>
