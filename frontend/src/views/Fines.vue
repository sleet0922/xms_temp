<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">罚金财务中心</h1>
        <p class="text-gray-600 mt-1">逾期罚金与赔偿结算</p>
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
            </button>
          </div>
        </div>
      </Card>

      <!-- Fines Table -->
      <Card padding="none">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">读者</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">图书</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">事由</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">金额</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="fine in fines" :key="fine.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm text-gray-900">{{ fine.user?.full_name }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ fine.borrow?.book?.title }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="getReasonVariant(fine.reason)" size="small">
                    {{ getReasonLabel(fine.reason) }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-sm font-medium text-gray-900">¥{{ parseFloat(fine.amount).toFixed(2) }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="getStatusVariant(fine.status)" size="small">
                    {{ getStatusLabel(fine.status) }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right space-x-2">
                  <Button
                    v-if="fine.status === 'unpaid' && userStore.isLibrarian"
                    size="small"
                    variant="primary"
                    @click="openSettleDialog(fine, 'paid')"
                  >
                    实收
                  </Button>
                  <Button
                    v-if="fine.status === 'unpaid' && userStore.isLibrarian"
                    size="small"
                    variant="outline"
                    @click="openSettleDialog(fine, 'waived')"
                  >
                    减免
                  </Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Settle Dialog -->
      <Dialog v-model="showSettleDialog" title="结算罚金" max-width="md">
        <div v-if="selectedFine" class="space-y-4">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-1">读者</div>
            <div class="font-medium">{{ selectedFine.user?.full_name }}</div>
            <div class="text-sm text-gray-600 mt-2 mb-1">罚金金额</div>
            <div class="text-2xl font-bold text-gray-900">¥{{ parseFloat(selectedFine.amount).toFixed(2) }}</div>
          </div>

          <Textarea v-model="settleNote" label="备注" rows="3" placeholder="可选：填写结算备注" />

          <div class="flex justify-end gap-3">
            <Button variant="outline" @click="showSettleDialog = false">取消</Button>
            <Button variant="primary" @click="handleSettle" :loading="loading">
              确认{{ settleAction === 'paid' ? '实收' : '减免' }}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Textarea from '@/components/ui/Textarea.vue'
import { finesApi } from '@/api'

const userStore = useUserStore()

const fines = ref([])
const activeStatus = ref('all')
const loading = ref(false)

const showSettleDialog = ref(false)
const selectedFine = ref(null)
const settleAction = ref('paid')
const settleNote = ref('')

const statusFilters = [
  { label: '全部', value: 'all' },
  { label: '待结清', value: 'unpaid' },
  { label: '已收缴', value: 'paid' },
  { label: '已减免', value: 'waived' }
]

const getReasonLabel = (reason) => {
  const labels = { overdue: '逾期滞纳', damage: '图书损坏', lost: '图书遗失' }
  return labels[reason] || reason
}

const getReasonVariant = (reason) => {
  const variants = { overdue: 'warning', damage: 'danger', lost: 'danger' }
  return variants[reason] || 'default'
}

const getStatusLabel = (status) => {
  const labels = { unpaid: '待结清', paid: '已收缴', waived: '已减免' }
  return labels[status] || status
}

const getStatusVariant = (status) => {
  const variants = { unpaid: 'warning', paid: 'success', waived: 'default' }
  return variants[status] || 'default'
}

const loadFines = async () => {
  loading.value = true
  try {
    const params = {
      status_filter: activeStatus.value === 'all' ? null : activeStatus.value
    }
    const response = await finesApi.getList(params)
    fines.value = response.data
  } catch (err) {
    window.$toast?.error('加载罚金记录失败')
  } finally {
    loading.value = false
  }
}

const openSettleDialog = (fine, action) => {
  selectedFine.value = fine
  settleAction.value = action
  settleNote.value = ''
  showSettleDialog.value = true
}

const handleSettle = async () => {
  loading.value = true
  try {
    await finesApi.settle(selectedFine.value.id, {
      action: settleAction.value,
      note: settleNote.value
    })
    window.$toast?.success(`罚金已${settleAction.value === 'paid' ? '收缴' : '减免'}`)
    showSettleDialog.value = false
    loadFines()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '结算失败')
  } finally {
    loading.value = false
  }
}

watch(activeStatus, () => {
  loadFines()
})

onMounted(() => {
  loadFines()
})
</script>
