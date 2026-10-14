<template>
  <div class="neo-page">
    <PageHeader title="借还工作台" subtitle="扫码办理借书、还书与续借">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="refreshing" @click="refreshAll">
          刷新数据
        </Button>
      </template>
    </PageHeader>

    <!-- 今日流通概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
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
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <Card class="group" hover>
        <div class="flex items-start gap-4 mb-5">
          <div
            class="neo-action-icon neo-action-icon-primary"
          >
            <ArrowUpTrayIcon class="w-6 h-6" />
          </div>
          <div class="min-w-0">
            <h2 class="text-base font-medium text-gray-900">借书办理</h2>
            <p class="text-sm text-gray-600 mt-1">选择读者与图书即可办理，也可直接扫码</p>
          </div>
        </div>

        <div class="space-y-4">
          <!-- 读者：下拉搜索选择，馆员无需手打卡号 -->
          <div ref="readerPickerRef" class="relative">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              读者 <span class="text-red-500">*</span>
            </label>

            <div
              v-if="selectedReader"
              class="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2"
            >
              <span class="text-sm font-medium text-gray-900">{{ selectedReader.full_name }}</span>
              <span class="text-xs font-mono text-gray-600">{{ selectedReader.card_number }}</span>
              <Badge :variant="selectedReader.status === 'active' ? 'success' : 'danger'" size="small">
                {{ selectedReader.status === 'active' ? '状态正常' : '卡已冻结' }}
              </Badge>
              <span class="text-xs text-gray-600">可借 {{ selectedReader.max_borrow_limit }} 册</span>
              <button
                type="button"
                class="ml-auto text-xs font-medium text-blue-700 hover:text-blue-900 transition-colors duration-150"
                @click="clearReader"
              >
                更换读者
              </button>
            </div>

            <template v-else>
              <Input
                v-model="readerQuery"
                placeholder="点击选择读者，或输入姓名/卡号搜索"
                :prepend-icon="MagnifyingGlassIcon"
                @focus="openReaderOptions"
                @input="onReaderSearch"
                @keyup.enter="pickExactReader"
              />
              <div
                v-if="readerOptionsOpen"
                class="absolute z-10 mt-1 w-full max-h-60 overflow-auto scrollbar-thin rounded-lg bg-white py-1 shadow-md border border-gray-200"
              >
                <div v-if="readersLoading" class="px-4 py-2 text-sm text-gray-500">正在加载读者…</div>
                <template v-else-if="readerOptions.length">
                  <button
                    v-for="item in readerOptions"
                    :key="item.id"
                    type="button"
                    class="w-full flex items-center gap-3 px-4 py-2 text-left transition-colors duration-150 hover:bg-blue-50"
                    @click="selectReader(item)"
                  >
                    <span class="text-sm text-gray-900">{{ item.full_name }}</span>
                    <span class="text-xs font-mono text-gray-500">{{ item.card_number }}</span>
                    <Badge v-if="item.status !== 'active'" variant="danger" size="small" class="ml-auto">
                      卡已冻结
                    </Badge>
                  </button>
                </template>
                <div v-else class="px-4 py-2 text-sm text-gray-500">没有匹配的读者</div>
              </div>
            </template>
          </div>

          <!-- 图书：从图书详情跳转则自动带入，否则扫码 -->
          <div v-if="selectedBook" class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-xs text-gray-500">本次办理</p>
                <p class="text-sm font-medium text-gray-900 truncate">《{{ selectedBook.title }}》</p>
                <p class="text-xs text-gray-600 mt-0.5">
                  在架 {{ selectedBook.available_copies }}/{{ selectedBook.total_copies }} 册 · 系统自动分配在架复本
                </p>
              </div>
              <button
                type="button"
                class="flex-shrink-0 text-xs font-medium text-blue-700 hover:text-blue-900 transition-colors duration-150"
                @click="clearSelectedBook"
              >
                改为扫码
              </button>
            </div>
          </div>
          <Input
            v-else
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
            :disabled="!selectedReader || !(selectedBook || borrowForm.barcode)"
            @click="handleBorrow"
          >
            确认借出
          </Button>
        </div>
      </Card>

      <Card class="group" hover>
        <div class="flex items-start gap-4 mb-5">
          <div
            class="neo-action-icon neo-action-icon-success"
          >
            <ArrowDownTrayIcon class="w-6 h-6" />
          </div>
          <div class="min-w-0">
            <h2 class="text-base font-medium text-gray-900">还书办理</h2>
            <p class="text-sm text-gray-600 mt-1">选择在借图书即可归还，逾期将自动生成罚金单</p>
          </div>
        </div>

        <div class="space-y-4">
          <!-- 在借图书：下拉选择，无需编条码 -->
          <div ref="returnPickerRef" class="relative">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              在借图书 <span class="text-red-500">*</span>
            </label>

            <div v-if="selectedReturn" class="rounded-lg border border-green-200 bg-green-50 px-3 py-2">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">
                    《{{ selectedReturn.book?.title || '-' }}》
                  </p>
                  <p class="text-xs text-gray-600 mt-0.5">
                    {{ selectedReturn.user?.full_name }}
                    · <span class="font-mono">{{ selectedReturn.user?.card_number }}</span>
                  </p>
                </div>
                <button
                  type="button"
                  class="flex-shrink-0 text-xs font-medium text-green-700 hover:text-green-900 transition-colors duration-150"
                  @click="clearReturnRecord"
                >
                  更换图书
                </button>
              </div>
              <div class="mt-2 flex flex-wrap items-center gap-2">
                <Badge :variant="isOverdue(selectedReturn) ? 'danger' : 'primary'" size="small">
                  {{ isOverdue(selectedReturn) ? `逾期 ${selectedReturn.overdue_days} 天` : '按期归还' }}
                </Badge>
                <span class="text-xs text-gray-600">应还 {{ formatDate(selectedReturn.due_date) }}</span>
                <span class="text-xs text-gray-500 font-mono">{{ selectedReturn.copy?.barcode }}</span>
              </div>
            </div>

            <template v-else-if="returnScanMode">
              <Input
                v-model="returnForm.barcode"
                placeholder="扫描图书条形码"
                :prepend-icon="QrCodeIcon"
                hint="扫码枪回车即提交"
                @keyup.enter="handleReturn"
              />
              <button
                type="button"
                class="mt-2 text-xs font-medium text-blue-700 hover:text-blue-900 transition-colors duration-150"
                @click="returnScanMode = false"
              >
                改为选择在借图书
              </button>
            </template>

            <template v-else>
              <Input
                v-model="returnQuery"
                placeholder="点击选择在借图书，或输入书名/读者搜索"
                :prepend-icon="MagnifyingGlassIcon"
                @focus="openReturnOptions"
                @input="onReturnSearch"
                @keyup.enter="pickExactReturn"
              />
              <div
                v-if="returnOptionsOpen"
                class="absolute z-10 mt-1 w-full max-h-60 overflow-auto scrollbar-thin rounded-lg bg-white py-1 shadow-md border border-gray-200"
              >
                <div v-if="returnsLoading" class="px-4 py-2 text-sm text-gray-500">正在加载在借图书…</div>
                <template v-else-if="returnOptions.length">
                  <button
                    v-for="record in returnOptions"
                    :key="record.id"
                    type="button"
                    class="w-full px-4 py-2 text-left transition-colors duration-150 hover:bg-green-50"
                    @click="selectReturn(record)"
                  >
                    <div class="flex items-center gap-2">
                      <span class="text-sm text-gray-900 truncate">{{ record.book?.title || '-' }}</span>
                      <Badge v-if="isOverdue(record)" variant="danger" size="small" class="ml-auto flex-shrink-0">
                        逾期 {{ record.overdue_days }} 天
                      </Badge>
                    </div>
                    <div class="text-xs text-gray-500 mt-0.5">
                      {{ record.user?.full_name }}
                      · <span class="font-mono">{{ record.user?.card_number }}</span>
                      · 应还 {{ formatDate(record.due_date) }}
                    </div>
                  </button>
                </template>
                <div v-else class="px-4 py-2 text-sm text-gray-500">没有匹配的在借图书</div>
              </div>
              <button
                type="button"
                class="mt-2 text-xs font-medium text-blue-700 hover:text-blue-900 transition-colors duration-150"
                @click="returnScanMode = true"
              >
                改为扫码
              </button>
            </template>
          </div>

          <Button
            variant="primary"
            size="large"
            block
            :loading="returnLoading"
            :disabled="!selectedReturn && !returnForm.barcode"
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
          <h2 class="text-base font-medium text-gray-900">本次操作结果</h2>
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
        <h2 class="text-base font-medium text-gray-900">最近流通流水</h2>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ArrowUpTrayIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  QrCodeIcon
} from '@heroicons/vue/24/outline'
import { booksApi, borrowsApi, circulationApi, finesApi, readersApi, statsApi } from '@/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Badge from '@/components/ui/Badge.vue'
import Alert from '@/components/ui/Alert.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const route = useRoute()
const router = useRouter()

const overview = ref({})
const records = ref([])
const recordsLoading = ref(false)
const refreshing = ref(false)

const borrowForm = reactive({ barcode: '' })
const returnForm = reactive({ barcode: '' })

const borrowLoading = ref(false)
const returnLoading = ref(false)
const renewingId = ref(null)

// 读者选择：下拉列表 + 关键字搜索，馆员无需手打卡号
const selectedReader = ref(null)
const readerQuery = ref('')
const readerOptions = ref([])
const readerOptionsOpen = ref(false)
const readersLoading = ref(false)
const readerPickerRef = ref(null)
let readerSearchTimer = null

// 图书来源：从图书详情页跳转时自动带入，否则走扫码
const selectedBook = ref(null)

// 还书：下拉选择在借图书（含逾期），也可切换为扫码
const selectedReturn = ref(null)
const returnQuery = ref('')
const returnOptions = ref([])
const returnOptionsOpen = ref(false)
const returnsLoading = ref(false)
const returnScanMode = ref(false)
const returnPickerRef = ref(null)
const returnableAll = ref([])

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

// 读者下拉：聚焦即列出读者，输入则按姓名/卡号实时搜索
async function loadReaders(search = '') {
  readersLoading.value = true
  try {
    const { data } = await readersApi.getList({ search: search || undefined, limit: 20 })
    readerOptions.value = data
  } catch (err) {
    readerOptions.value = []
  } finally {
    readersLoading.value = false
  }
}

function openReaderOptions() {
  readerOptionsOpen.value = true
  if (!readerOptions.value.length) loadReaders()
}

function onReaderSearch() {
  readerOptionsOpen.value = true
  clearTimeout(readerSearchTimer)
  readerSearchTimer = setTimeout(() => loadReaders(readerQuery.value.trim()), 250)
}

function selectReader(reader) {
  selectedReader.value = reader
  readerOptionsOpen.value = false
  readerQuery.value = ''
}

function clearReader() {
  selectedReader.value = null
  readerQuery.value = ''
  readerOptions.value = []
}

// 兼容扫码枪：回车时若输入恰好是某个卡号则直接选中
function pickExactReader() {
  const value = readerQuery.value.trim()
  if (!value) return
  const matched = readerOptions.value.find((item) => item.card_number === value)
  if (matched) {
    selectReader(matched)
    return
  }
  window.$toast?.warning('未匹配到该卡号的读者，请从下拉列表中选择')
}

// 从图书详情页跳转时带过来的书目：无需再扫条码
async function loadSelectedBook() {
  const bookId = Number(route.query.bookId)
  if (!bookId) {
    selectedBook.value = null
    return
  }
  try {
    const { data } = await booksApi.getById(bookId)
    selectedBook.value = data
  } catch (err) {
    selectedBook.value = null
    window.$toast?.error('未找到待办理的图书')
  }
}

function clearSelectedBook() {
  selectedBook.value = null
  router.replace({ path: '/admin/circulation' })
}

// 在借图书下拉：首屏预取最近若干条，输入关键字时改为服务端检索，
// 后端 /api/borrows?search= 已支持按书名 / 读者姓名 / 用户名 / 借书卡号匹配，
// 因此不再受固定条数限制、也不会漏掉较早的未归还记录。
const RETURN_PAGE_SIZE = 50
let returnSearchTimer = null

async function loadReturnable(keyword = '') {
  returnsLoading.value = true
  try {
    const params = { status_filter: 'unreturned', limit: RETURN_PAGE_SIZE }
    const kw = keyword.trim()
    if (kw) params.search = kw
    const { data } = await borrowsApi.getList(params)
    returnableAll.value = data
    returnOptions.value = data
  } catch (err) {
    returnableAll.value = []
    returnOptions.value = []
  } finally {
    returnsLoading.value = false
  }
}

function openReturnOptions() {
  returnOptionsOpen.value = true
  if (!returnableAll.value.length) loadReturnable(returnQuery.value)
}

function onReturnSearch() {
  returnOptionsOpen.value = true
  if (returnSearchTimer) clearTimeout(returnSearchTimer)
  returnSearchTimer = setTimeout(() => loadReturnable(returnQuery.value), 250)
}

function selectReturn(record) {
  selectedReturn.value = record
  returnOptionsOpen.value = false
  returnQuery.value = ''
}

function clearReturnRecord() {
  selectedReturn.value = null
  returnQuery.value = ''
  returnScanMode.value = false
}

// 回车：唯一匹配或条码完全一致时直接选中，否则提示改用扫码
function pickExactReturn() {
  const value = returnQuery.value.trim()
  if (!value) return
  const exact = returnOptions.value.find((record) => record.copy?.barcode === value)
  if (exact) {
    selectReturn(exact)
    return
  }
  if (returnOptions.value.length === 1) {
    selectReturn(returnOptions.value[0])
    return
  }
  window.$toast?.warning('未匹配到在借图书，可点击「改为扫码」直接归还')
}

async function handleBorrow() {
  const barcode = borrowForm.barcode.trim()
  if (!selectedReader.value) {
    window.$toast?.warning('请先选择读者')
    return
  }
  if (!selectedBook.value && !barcode) {
    window.$toast?.warning('请先扫描图书条码或从图书详情选择图书')
    return
  }

  borrowLoading.value = true
  errorMessage.value = ''
  try {
    const payload = { card_number: selectedReader.value.card_number }
    if (selectedBook.value) payload.book_id = selectedBook.value.id
    else payload.barcode = barcode

    const { data } = await circulationApi.borrow(payload)
    lastResult.value = { kind: 'borrow', record: data }
    window.$toast?.success('借出成功')
    borrowForm.barcode = ''
    // 一次办理完成，清掉带入的书目，避免重复借出
    if (selectedBook.value) clearSelectedBook()
    returnableAll.value = [] // 刚借出的书进入在借书单，下次展开重新拉取
    loadRecords()
    loadOverview()
  } catch (err) {
    lastResult.value = null
    errorMessage.value = err.response?.data?.detail || '借出失败，请核对读者与图书'
    window.$toast?.error(errorMessage.value)
  } finally {
    borrowLoading.value = false
  }
}

async function handleReturn() {
  const barcode = returnForm.barcode.trim()
  if (!selectedReturn.value && !barcode) {
    window.$toast?.warning('请先选择在借图书或扫描图书条码')
    return
  }

  returnLoading.value = true
  errorMessage.value = ''
  try {
    const payload = selectedReturn.value ? { record_id: selectedReturn.value.id } : { barcode }
    const { data } = await circulationApi.return(payload)
    // 归还接口已回填最终罚金与逾期天数，直接采用；仅在历史数据缺失时回退反查罚金单
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
    if (selectedReturn.value) clearReturnRecord()
    returnableAll.value = [] // 库存与在借书单已变化，下次展开重新拉取
    loadRecords()
    loadOverview()
  } catch (err) {
    lastResult.value = null
    errorMessage.value = err.response?.data?.detail || '归还失败，请核对所选图书'
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

// 路由带参变化时同步待办理图书（例如从另一本书的详情页再跳进来）
watch(() => route.query.bookId, loadSelectedBook)

// 点击面板外收起下拉，避免遮住下方按钮
function handleDocumentClick(event) {
  if (readerOptionsOpen.value && !readerPickerRef.value?.contains(event.target)) {
    readerOptionsOpen.value = false
  }
  if (returnOptionsOpen.value && !returnPickerRef.value?.contains(event.target)) {
    returnOptionsOpen.value = false
  }
}

onMounted(() => {
  refreshAll()
  loadSelectedBook()
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>
