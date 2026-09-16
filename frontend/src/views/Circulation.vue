<template>
  <div class="p-6 lg:p-8 max-w-7xl mx-auto">
    <PageHeader title="智慧借还服务台" subtitle="扫码即借、即还，逾期自动核算罚金">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="refreshing" @click="refreshAll">
          刷新数据
        </Button>
      </template>
    </PageHeader>

    <!-- 今日流通概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
      <StatCard
        label="今日借出"
        :value="overview.today_borrows ?? 0"
        hint="今日办理的借出册数"
        :icon="ArrowUpTrayIcon"
        tone="primary"
      />
      <StatCard
        label="今日归还"
        :value="overview.today_returns ?? 0"
        hint="今日完成的归还册数"
        :icon="ArrowDownTrayIcon"
        tone="success"
      />
      <StatCard
        label="逾期未还"
        :value="overview.overdue_borrows ?? 0"
        hint="已过应还日期仍在读者手中"
        :icon="ExclamationTriangleIcon"
        tone="danger"
      />
    </div>

    <!-- 借书 / 还书操作台 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <Card class="group" hover>
        <div class="flex items-start gap-4 mb-5">
          <div
            class="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0 transition-all duration-200 ease-out group-hover:bg-blue-500 group-hover:scale-110"
          >
            <ArrowUpTrayIcon class="w-6 h-6 text-blue-600 transition-colors duration-200 group-hover:text-white" />
          </div>
          <div class="min-w-0">
            <h2 class="text-lg font-semibold tracking-tight text-gray-900">借书办理</h2>
            <p class="text-sm text-gray-600 mt-1">先扫读者卡号，再扫图书条码即可完成借出</p>
          </div>
        </div>

        <div class="space-y-4">
          <Input
            v-model="borrowForm.cardNumber"
            label="读者卡号"
            placeholder="扫描或输入借书卡号"
            :prepend-icon="IdentificationIcon"
            required
            @blur="lookupReader"
            @keyup.enter="handleBorrow"
          />
          <div
            v-if="readerInfo"
            class="flex flex-wrap items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2"
          >
            <span class="text-sm font-medium text-gray-900">{{ readerInfo.full_name }}</span>
            <span class="text-sm text-gray-600">可借额度 {{ readerInfo.max_borrow_limit }} 册</span>
            <Badge :variant="readerInfo.status === 'active' ? 'success' : 'danger'" size="small">
              {{ readerInfo.status === 'active' ? '状态正常' : '卡已冻结' }}
            </Badge>
          </div>

          <Input
            v-model="borrowForm.barcode"
            label="图书条码"
            placeholder="扫描图书条形码"
            :prepend-icon="QrCodeIcon"
            required
            hint="扫码枪回车即提交"
            @keyup.enter="handleBorrow"
          />

          <Button
            variant="primary"
            size="large"
            block
            :loading="borrowLoading"
            :disabled="!borrowForm.cardNumber || !borrowForm.barcode"
            @click="handleBorrow"
          >
            确认借出
          </Button>
        </div>
      </Card>

      <Card class="group" hover>
        <div class="flex items-start gap-4 mb-5">
          <div
            class="w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0 transition-all duration-200 ease-out group-hover:bg-green-500 group-hover:scale-110"
          >
            <ArrowDownTrayIcon class="w-6 h-6 text-green-600 transition-colors duration-200 group-hover:text-white" />
          </div>
          <div class="min-w-0">
            <h2 class="text-lg font-semibold tracking-tight text-gray-900">还书办理</h2>
            <p class="text-sm text-gray-600 mt-1">扫描图书条码，逾期将自动生成罚金单</p>
          </div>
        </div>

        <div class="space-y-4">
          <Input
            v-model="returnForm.barcode"
            label="图书条码"
            placeholder="扫描图书条形码"
            :prepend-icon="QrCodeIcon"
            required
            hint="扫码枪回车即提交"
            @keyup.enter="handleReturn"
          />

          <Button
            variant="primary"
            size="large"
            block
            :loading="returnLoading"
            :disabled="!returnForm.barcode"
            @click="handleReturn"
          >
            确认归还
          </Button>

          <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
            <p class="text-sm text-gray-600">
              归还前请确认图书是否有破损；系统按应还日期实时核算逾期天数与罚金金额。
            </p>
          </div>
        </div>
      </Card>
    </div>

    <!-- 本次操作结果 -->
    <Card v-if="lastResult" class="mb-6">
      <div class="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h2 class="text-lg font-semibold tracking-tight text-gray-900">本次操作结果</h2>
          <p class="text-sm text-gray-600 mt-1">
            {{ lastResult.kind === 'borrow' ? '借出手续已办理完成' : '归还手续已办理完成' }}
          </p>
        </div>
        <Badge :variant="lastResult.kind === 'borrow' ? 'success' : 'primary'">
          {{ lastResult.kind === 'borrow' ? '借出成功' : '归还成功' }}
        </Badge>
      </div>

      <dl class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="item in resultFields"
          :key="item.label"
          class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
        >
          <dt class="text-xs text-gray-500">{{ item.label }}</dt>
          <dd class="text-sm font-medium mt-1" :class="item.class || 'text-gray-900'">{{ item.value }}</dd>
        </div>
      </dl>
    </Card>

    <!-- 失败原因 -->
    <Alert
      v-if="errorMessage"
      class="mb-6"
      variant="error"
      title="操作未完成"
      :message="errorMessage"
    />

    <!-- 最近流通流水 -->
    <Card padding="none">
      <div class="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold tracking-tight text-gray-900">最近流通流水</h2>
        <span class="text-xs text-gray-500">
          {{ recordsLoading ? '加载中…' : `最近 ${records.length} 条借阅记录` }}
        </span>
      </div>

      <div v-if="recordsLoading" class="px-6 py-6 text-sm text-gray-500">正在加载流通流水…</div>

      <div v-else-if="records.length" class="overflow-x-auto scrollbar-thin">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">图书</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">读者</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">借出日期</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">应还日期</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
              <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="record in records" :key="record.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 text-sm font-medium text-gray-900 max-w-xs truncate">
                {{ record.book?.title || '-' }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">
                <div>{{ record.user?.full_name || '-' }}</div>
                <div class="text-xs text-gray-500 font-mono">{{ record.user?.card_number || '' }}</div>
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(record.borrow_date) }}</td>
              <td
                class="px-4 py-3 text-sm"
                :class="isOverdue(record) ? 'text-red-600 font-medium' : 'text-gray-600'"
              >
                {{ formatDate(record.due_date) }}
                <span v-if="isOverdue(record)" class="ml-1 text-xs">逾期 {{ record.overdue_days }} 天</span>
              </td>
              <td class="px-4 py-3">
                <Badge :variant="statusVariant(record.status)" size="small">
                  {{ statusLabel(record.status) }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right">
                <Button
                  v-if="!record.return_date"
                  size="small"
                  variant="ghost"
                  :loading="renewingId === record.id"
                  @click="handleRenew(record)"
                >
                  续借
                </Button>
                <span v-else class="text-xs text-gray-400">已归还</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <EmptyState
        v-else
        title="暂无流通流水"
        description="完成一次借书或还书后，记录会显示在这里"
        :icon="ClockIcon"
      />
    </Card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ArrowUpTrayIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  IdentificationIcon,
  QrCodeIcon
} from '@heroicons/vue/24/outline'
import { borrowsApi, circulationApi, finesApi, readersApi, statsApi } from '@/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Badge from '@/components/ui/Badge.vue'
import Alert from '@/components/ui/Alert.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const overview = ref({})
const records = ref([])
const recordsLoading = ref(false)
const refreshing = ref(false)

const borrowForm = reactive({ cardNumber: '', barcode: '' })
const returnForm = reactive({ barcode: '' })

const borrowLoading = ref(false)
const returnLoading = ref(false)
const renewingId = ref(null)

const readerInfo = ref(null)
const lastResult = ref(null)
const errorMessage = ref('')

const STATUS_MAP = {
  borrowed: { label: '在借', variant: 'primary' },
  overdue: { label: '逾期', variant: 'danger' },
  returned: { label: '已归还', variant: 'success' },
  lost: { label: '遗失', variant: 'warning' }
}

const statusLabel = (status) => STATUS_MAP[status]?.label || status || '-'
const statusVariant = (status) => STATUS_MAP[status]?.variant || 'default'

const formatDate = (value) => (value ? new Date(value).toLocaleDateString('zh-CN') : '-')
const formatDateTime = (value) =>
  value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
const isOverdue = (record) =>
  !record.return_date && record.due_date && new Date(record.due_date) < new Date()

// 本次操作结果按借/还分别展示不同字段
const resultFields = computed(() => {
  const result = lastResult.value
  if (!result) return []
  const record = result.record
  const fields = [
    { label: '图书', value: record.book?.title || '-' },
    { label: '作者', value: record.book?.author || '-' },
    { label: '图书条码', value: record.copy?.barcode || '-', class: 'text-gray-900 font-mono' },
    { label: '读者', value: record.user?.full_name || '-' },
    { label: '读者卡号', value: record.user?.card_number || '-', class: 'text-gray-900 font-mono' }
  ]

  if (result.kind === 'borrow') {
    fields.push(
      { label: '借出时间', value: formatDateTime(record.borrow_date) },
      { label: '应还日期', value: formatDate(record.due_date), class: 'text-blue-700' }
    )
  } else {
    fields.push(
      { label: '归还时间', value: formatDateTime(record.return_date) },
      { label: '应还日期', value: formatDate(record.due_date) },
      {
        label: '逾期罚金',
        value: result.fineAmount > 0 ? `¥${Number(result.fineAmount).toFixed(2)}` : '无罚金',
        class: result.fineAmount > 0 ? 'text-red-600' : 'text-green-600'
      }
    )
  }

  return fields
})

async function loadOverview() {
  try {
    const { data } = await statsApi.getOverview()
    overview.value = data
  } catch (err) {
    window.$toast?.error('加载流通指标失败')
  }
}

async function loadRecords() {
  recordsLoading.value = true
  try {
    const { data } = await borrowsApi.getList({ limit: 10 })
    records.value = data
  } catch (err) {
    window.$toast?.error('加载流通流水失败')
  } finally {
    recordsLoading.value = false
  }
}

async function refreshAll() {
  refreshing.value = true
  await Promise.all([loadOverview(), loadRecords()])
  refreshing.value = false
}

// 卡号失焦时预检读者，便于馆员确认借阅资格
async function lookupReader() {
  const card = borrowForm.cardNumber.trim()
  readerInfo.value = null
  if (!card) return
  try {
    const { data } = await readersApi.getList({ search: card, limit: 5 })
    readerInfo.value = data.find((item) => item.card_number === card) || null
  } catch (err) {
    readerInfo.value = null
  }
}

async function handleBorrow() {
  const cardNumber = borrowForm.cardNumber.trim()
  const barcode = borrowForm.barcode.trim()
  if (!cardNumber || !barcode) {
    window.$toast?.warning('请先扫描读者卡号与图书条码')
    return
  }

  borrowLoading.value = true
  errorMessage.value = ''
  try {
    const { data } = await circulationApi.borrow(cardNumber, barcode)
    lastResult.value = { kind: 'borrow', record: data }
    window.$toast?.success('借出成功')
    borrowForm.barcode = ''
    // 借出后条码框保持聚焦，方便连续扫码
    loadRecords()
    loadOverview()
  } catch (err) {
    lastResult.value = null
    errorMessage.value = err.response?.data?.detail || '借出失败，请核对卡号与条码'
    window.$toast?.error(errorMessage.value)
  } finally {
    borrowLoading.value = false
  }
}

async function handleReturn() {
  const barcode = returnForm.barcode.trim()
  if (!barcode) {
    window.$toast?.warning('请先扫描图书条码')
    return
  }

  returnLoading.value = true
  errorMessage.value = ''
  try {
    const { data } = await circulationApi.return(barcode)
    // 接口回传记录不含罚金金额，逾期时按记录反查自动生成的罚金单
    let fineAmount = Number(data.calculated_fine || 0)
    const overdue = data.return_date && data.due_date && new Date(data.return_date) > new Date(data.due_date)
    if (overdue && !fineAmount) {
      try {
        const { data: fines } = await finesApi.getList({ user_id: data.user_id })
        const matched = fines.find((fine) => fine.borrow_id === data.id)
        if (matched) fineAmount = Number(matched.amount || 0)
      } catch (err) {
        fineAmount = 0
      }
    }

    lastResult.value = { kind: 'return', record: data, fineAmount }
    window.$toast?.success(
      fineAmount > 0 ? `归还成功，产生逾期罚金 ¥${fineAmount.toFixed(2)}` : '归还成功，无罚金'
    )
    returnForm.barcode = ''
    loadRecords()
    loadOverview()
  } catch (err) {
    lastResult.value = null
    errorMessage.value = err.response?.data?.detail || '归还失败，请核对图书条码'
    window.$toast?.error(errorMessage.value)
  } finally {
    returnLoading.value = false
  }
}

async function handleRenew(record) {
  renewingId.value = record.id
  try {
    await circulationApi.renew(record.id)
    window.$toast?.success('续借成功，应还日期已顺延')
    await Promise.all([loadRecords(), loadOverview()])
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '续借失败')
  } finally {
    renewingId.value = null
  }
}

// 卡号变动后旧读者信息失效，避免误判借阅资格
watch(
  () => borrowForm.cardNumber,
  () => {
    readerInfo.value = null
  }
)

onMounted(() => {
  refreshAll()
})
</script>