<template>
  <div class="p-6 lg:p-8 max-w-7xl mx-auto">
    <PageHeader
      title="罚金账务中心"
      subtitle="逾期滞纳、损坏赔偿的账单结算与催缴管理"
    >
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadData">
          刷新数据
        </Button>
      </template>
    </PageHeader>

    <!-- 账务概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <StatCard
        label="未缴总额"
        :value="`¥${money(summary.amount.unpaid)}`"
        :hint="`${summary.count.unpaid} 笔待结清`"
        :icon="ExclamationTriangleIcon"
        tone="danger"
      />
      <StatCard
        label="已缴总额"
        :value="`¥${money(summary.amount.paid)}`"
        :hint="`${summary.count.paid} 笔已收缴`"
        :icon="CheckCircleIcon"
        tone="success"
      />
      <StatCard
        label="减免总额"
        :value="`¥${money(summary.amount.waived)}`"
        :hint="`${summary.count.waived} 笔已减免`"
        :icon="ShieldCheckIcon"
        tone="warning"
      />
      <StatCard
        label="我的未缴"
        :value="`¥${money(overview.user_fines)}`"
        hint="仅统计本人名下账单"
        :icon="UserCircleIcon"
        tone="primary"
      />
    </div>

    <!-- 状态筛选 -->
    <div class="mb-4">
      <Tabs v-model="activeStatus" :tabs="['全部', '未缴', '已缴', '已减免']" />
    </div>

    <!-- 账单表格 -->
    <Card padding="none">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th v-if="userStore.isLibrarian" class="px-4 py-3 text-left text-xs font-semibold text-gray-600">读者</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">事由</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">金额</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">产生日期</th>
              <th v-if="userStore.isLibrarian" class="px-4 py-3 text-left text-xs font-semibold text-gray-600">处理备注</th>
              <th v-if="userStore.isLibrarian" class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="fine in fines" :key="fine.id" class="hover:bg-gray-50 transition-colors">
              <td v-if="userStore.isLibrarian" class="px-4 py-3 text-sm">
                <div class="font-medium text-gray-900">{{ fine.user?.full_name || fine.user?.username || '-' }}</div>
                <div class="text-xs text-gray-500 font-mono">{{ fine.user?.card_number || '—' }}</div>
              </td>
              <td class="px-4 py-3 text-sm">
                <div class="text-gray-900">{{ reasonLabel(fine.reason) }}</div>
                <div v-if="fine.borrow_id" class="text-xs text-gray-500 font-mono">借阅 #{{ fine.borrow_id }}</div>
              </td>
              <td class="px-4 py-3 text-sm font-medium text-gray-900">¥{{ money(fine.amount) }}</td>
              <td class="px-4 py-3">
                <Badge :variant="statusVariant(fine.status)" size="small">{{ statusLabel(fine.status) }}</Badge>
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(fine.created_at) }}</td>
              <td v-if="userStore.isLibrarian" class="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{{ fine.notes || '—' }}</td>
              <td v-if="userStore.isLibrarian" class="px-4 py-3">
                <div class="flex items-center justify-end gap-2">
                  <template v-if="fine.status === 'unpaid'">
                    <Button size="small" variant="primary" @click="openSettleDialog(fine)">结清/减免</Button>
                    <Button size="small" variant="outline" @click="handleRemind(fine)">催缴</Button>
                  </template>
                  <span v-else class="text-xs text-gray-500">—</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="loading" class="py-12 text-center text-sm text-gray-500">加载中…</div>
      <EmptyState
        v-else-if="fines.length === 0"
        title="暂无罚金账单"
        description="当前筛选条件下没有记录，保持按时归还就不会产生罚金。"
        :icon="BanknotesIcon"
      />
    </Card>

    <!-- 结算对话框 -->
    <Dialog v-model="showSettleDialog" title="结算罚金账单" max-width="md">
      <div v-if="settleTarget" class="space-y-4">
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-600">读者</div>
          <div class="font-medium text-gray-900 mt-1">
            {{ settleTarget.user?.full_name || settleTarget.user?.username || '—' }}
          </div>
          <div class="text-sm text-gray-600 mt-3">应结金额</div>
          <div class="text-2xl font-semibold tracking-tight text-gray-900 mt-1">¥{{ money(settleTarget.amount) }}</div>
        </div>

        <div>
          <span class="block text-sm font-medium text-gray-700 mb-2">处理方式</span>
          <div class="flex gap-3">
            <Button
              :variant="settleForm.waive ? 'outline' : 'primary'"
              :aria-pressed="!settleForm.waive"
              @click="settleForm.waive = false"
            >
              结清实收
            </Button>
            <Button
              :variant="settleForm.waive ? 'secondary' : 'outline'"
              :aria-pressed="settleForm.waive"
              @click="settleForm.waive = true"
            >
              特批减免
            </Button>
          </div>
        </div>

        <Textarea
          v-model="settleForm.notes"
          label="备注"
          rows="3"
          placeholder="可选：填写收款方式或减免依据"
          hint="将记录到账单备注中，便于后续对账"
        />
      </div>

      <template #footer>
        <Button variant="outline" @click="showSettleDialog = false">取消</Button>
        <Button
          :variant="settleForm.waive ? 'secondary' : 'primary'"
          :loading="settling"
          @click="handleSettle"
        >
          确认{{ settleForm.waive ? '减免' : '结清' }}
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import {
  ArrowPathIcon,
  BanknotesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  UserCircleIcon
} from '@heroicons/vue/24/outline'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Tabs from '@/components/ui/Tabs.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Textarea from '@/components/ui/Textarea.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { finesApi, statsApi } from '@/api'

const userStore = useUserStore()

// Tabs 索引 → 后端 status_filter 参数
const STATUS_PARAMS = [null, 'unpaid', 'paid', 'waived']

const REASON_LABELS = { overdue: '逾期滞纳', damage: '图书损坏', lost: '图书遗失' }
const STATUS_LABELS = { unpaid: '未缴', paid: '已缴', waived: '减免' }
const STATUS_VARIANTS = { unpaid: 'danger', paid: 'success', waived: 'default' }

const fines = ref([])
const loading = ref(false)
const activeStatus = ref(0)

const summary = ref({
  amount: { unpaid: '0.00', paid: '0.00', waived: '0.00' },
  count: { unpaid: 0, paid: 0, waived: 0 }
})
const overview = ref({ user_fines: '0.00' })

const showSettleDialog = ref(false)
const settleTarget = ref(null)
const settling = ref(false)
const settleForm = reactive({ waive: false, notes: '' })

const money = (value) => Number(value || 0).toFixed(2)
const reasonLabel = (reason) => REASON_LABELS[reason] || reason || '其他'
const statusLabel = (status) => STATUS_LABELS[status] || status
const statusVariant = (status) => STATUS_VARIANTS[status] || 'default'

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const loadFines = async () => {
  loading.value = true
  try {
    const params = {}
    if (STATUS_PARAMS[activeStatus.value]) {
      params.status_filter = STATUS_PARAMS[activeStatus.value]
    }
    const response = await finesApi.getList(params)
    fines.value = response.data
  } catch (err) {
    window.$toast?.error('加载罚金账单失败')
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  try {
    const [summaryRes, overviewRes] = await Promise.all([
      finesApi.getSummary(),
      statsApi.getOverview()
    ])
    summary.value = summaryRes.data
    overview.value = overviewRes.data
  } catch (err) {
    window.$toast?.error('加载罚金汇总失败')
  }
}

const loadData = async () => {
  await Promise.all([loadFines(), loadSummary()])
}

const openSettleDialog = (fine) => {
  settleTarget.value = fine
  settleForm.waive = false
  settleForm.notes = ''
  showSettleDialog.value = true
}

const handleSettle = async () => {
  settling.value = true
  try {
    // 后端 FinePayRequest：waive=false 结清实收 / waive=true 特批减免，notes 为备注
    await finesApi.settle(settleTarget.value.id, {
      waive: settleForm.waive,
      notes: settleForm.notes || null
    })
    window.$toast?.success(settleForm.waive ? '账单已减免' : '账单已结清')
    showSettleDialog.value = false
    await loadData()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '结算失败')
  } finally {
    settling.value = false
  }
}

const handleRemind = async (fine) => {
  try {
    const response = await finesApi.remind(fine.user_id)
    window.$toast?.success(response.data?.message || '催缴通知已发送')
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '催缴失败')
  }
}

watch(activeStatus, () => {
  loadFines()
})

onMounted(() => {
  loadData()
})
</script>