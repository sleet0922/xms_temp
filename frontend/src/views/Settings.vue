<template>
  <div class="neo-page p-6 lg:p-8 max-w-7xl mx-auto">
    <PageHeader title="系统设置与审计" subtitle="借阅规则配置、公告发布与操作留痕">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="refreshing" @click="loadAll">
          刷新
        </Button>
      </template>
    </PageHeader>

    <Card padding="normal">
      <Tabs :tabs="tabNames" v-model="activeTab">
        <!-- 1. 系统设置 -->
        <template #panel-0>
          <div v-if="settingsLoading" class="py-12 text-center text-sm text-gray-500">设置加载中…</div>
          <EmptyState v-else-if="!settings.length" title="暂无系统设置" description="尚未配置任何业务规则" />
          <div v-else class="divide-y divide-gray-200">
            <div
              v-for="item in settings"
              :key="item.key"
              class="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
            >
              <div class="min-w-0">
                <div class="text-sm font-medium text-gray-900">{{ metaOf(item.key).label }}</div>
                <div class="text-xs text-gray-500 mt-1">
                  {{ item.description || metaOf(item.key).desc }}
                  <span class="font-mono text-gray-400">（{{ item.key }}）</span>
                </div>
              </div>

              <div class="flex items-center gap-3 flex-shrink-0">
                <template v-if="isBoolValue(item.value)">
                  <Switch :model-value="isTrue(item.draft)" @update:modelValue="toggleBool(item, $event)" />
                  <span class="text-sm text-gray-600 w-10">{{ isTrue(item.draft) ? '启用' : '停用' }}</span>
                </template>
                <template v-else>
                  <Input v-model="item.draft" class="w-full sm:w-48" />
                  <Button
                    size="small"
                    variant="primary"
                    :loading="savingKey === item.key"
                    :disabled="String(item.draft) === String(item.value)"
                    @click="saveSetting(item)"
                  >
                    保存
                  </Button>
                </template>
              </div>
            </div>
          </div>
        </template>

        <!-- 2. 公告管理 -->
        <template #panel-1>
          <div class="flex items-center justify-between gap-4 mb-4">
            <div>
              <h3 class="text-lg font-semibold tracking-tight text-gray-900">馆内公告</h3>
              <p class="text-sm text-gray-600 mt-1">当前生效中的公告，共 {{ announcements.length }} 条</p>
            </div>
            <Button variant="primary" :prepend-icon="PlusIcon" @click="openAnnDialog">发布公告</Button>
          </div>

          <div v-if="annLoading" class="py-12 text-center text-sm text-gray-500">公告加载中…</div>
          <EmptyState v-else-if="!announcements.length" title="暂无公告" description="点击「发布公告」向全馆读者发布通知" />
          <div v-else class="divide-y divide-gray-200">
            <div v-for="ann in announcements" :key="ann.id" class="py-4 flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <Badge :variant="priorityVariant(ann.priority)" size="small">{{ priorityLabel(ann.priority) }}</Badge>
                  <span class="text-xs text-gray-500">{{ formatDateTime(ann.created_at) }}</span>
                </div>
                <div class="text-sm font-medium text-gray-900">{{ ann.title }}</div>
                <p class="text-sm text-gray-600 mt-1">{{ ann.content }}</p>
              </div>
              <Button size="small" variant="ghost" class="flex-shrink-0" @click="askDelete(ann)">删除</Button>
            </div>
          </div>
        </template>

        <!-- 3. 审计日志 -->
        <template #panel-2>
          <div class="flex items-center justify-between gap-4 mb-4">
            <h3 class="text-lg font-semibold tracking-tight text-gray-900">操作审计日志</h3>
            <div class="w-56 flex-shrink-0">
              <Select v-model="actionSelected" :options="actionOptions" placeholder="全部动作" />
            </div>
          </div>

          <div v-if="logsLoading" class="py-12 text-center text-sm text-gray-500">日志加载中…</div>
          <EmptyState v-else-if="!logs.length" title="暂无审计日志" description="符合条件的操作记录为空" />
          <div v-else>
            <div class="overflow-x-auto scrollbar-thin">
              <table class="w-full">
                <thead class="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">时间</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">操作人</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">动作</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">对象</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">详情</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">IP</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50 transition-colors">
                    <td class="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{{ formatDateTime(log.created_at) }}</td>
                    <td class="px-4 py-3 text-sm text-gray-900">{{ log.username || (log.user_id ? `#${log.user_id}` : '系统') }}</td>
                    <td class="px-4 py-3">
                      <Badge variant="default" size="small" class="font-mono">{{ log.action }}</Badge>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                      {{ log.target_type || '-' }}
                      <span v-if="log.target_id" class="font-mono">#{{ log.target_id }}</span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">{{ log.detail || '-' }}</td>
                    <td class="px-4 py-3 text-sm text-gray-500 font-mono whitespace-nowrap">{{ log.ip_address || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="mt-4">
              <Pagination
                :page="page"
                :page-size="PAGE_SIZE"
                :total="total"
                @update:page="changePage"
              />
            </div>
          </div>
        </template>

        <!-- 4. 系统信息 -->
        <template #panel-3>
          <h3 class="text-lg font-semibold tracking-tight text-gray-900 mb-4">系统运行信息</h3>
          <div v-if="infoLoading" class="py-12 text-center text-sm text-gray-500">系统信息加载中…</div>
          <EmptyState v-else-if="!infoRows.length" title="暂无系统信息" />
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="row in infoRows"
              :key="row.label"
              class="border border-gray-200 rounded-lg p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <div class="text-xs text-gray-500">{{ row.label }}</div>
              <div class="font-mono text-sm text-gray-900 mt-1 break-all">{{ row.value }}</div>
            </div>
          </div>
        </template>
      </Tabs>
    </Card>

    <!-- 发布公告 -->
    <Dialog v-model="annDialogOpen" title="发布公告" max-width="lg" persistent>
      <form class="space-y-4" @submit.prevent="submitAnnouncement">
        <Input v-model="annForm.title" label="公告标题" placeholder="请输入公告标题" required />
        <Textarea v-model="annForm.content" label="公告内容" rows="4" placeholder="请输入公告正文" required />
        <Select v-model="prioritySelected" :options="priorityOptions" label="优先级" required />
        <div class="flex justify-end gap-3">
          <Button variant="outline" @click="annDialogOpen = false">取消</Button>
          <Button type="submit" variant="primary" :loading="submitting">发布</Button>
        </div>
      </form>
    </Dialog>

    <!-- 删除确认 -->
    <Dialog v-model="deleteDialogOpen" title="删除公告" max-width="sm" persistent>
      <p class="text-sm text-gray-600">
        确认删除公告「{{ deletingAnn?.title }}」？该操作不可撤销。
      </p>
      <template #footer>
        <Button variant="outline" @click="deleteDialogOpen = false">取消</Button>
        <Button variant="danger" :loading="deleting" @click="confirmDelete">确认删除</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ArrowPathIcon, PlusIcon } from '@heroicons/vue/24/outline'
import PageHeader from '@/components/ui/PageHeader.vue'
import Card from '@/components/ui/Card.vue'
import Tabs from '@/components/ui/Tabs.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Switch from '@/components/ui/Switch.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Pagination from '@/components/ui/Pagination.vue'
import { systemApi, announcementsApi } from '@/api'

const PAGE_SIZE = 20
const tabNames = ['系统设置', '公告管理', '审计日志', '系统信息']

// 设置项显示名称与说明，未识别的 key 直接展示原始 key
const settingMeta = {
  library_name: { label: '图书馆名称', desc: '全馆展示使用的名称' },
  borrow_limit: { label: '借阅上限', desc: '单张借阅证可同时借阅的图书册数' },
  max_borrow_books: { label: '借阅上限', desc: '普通读者可同时借阅的图书册数' },
  loan_days: { label: '借期天数', desc: '新借图书的默认借阅天数' },
  default_borrow_days: { label: '借期天数', desc: '新借图书的默认借阅天数' },
  renew_days: { label: '续借天数', desc: '每次续借延长的天数' },
  max_renew_times: { label: '最大续借次数', desc: '同一本书允许续借的次数上限' },
  fine_rate: { label: '日罚金', desc: '逾期每天产生的罚金（元）' },
  daily_fine_rate: { label: '日罚金', desc: '逾期每天产生的罚金（元）' },
  reservation_expire_days: { label: '预约保留天数', desc: '预约到书后为读者保留的天数' },
  due_reminder_days: { label: '到期提醒提前天数', desc: '到期前多少天推送归还提醒' }
}

const activeTab = ref(0)
const refreshing = ref(false)

const settings = ref([])
const settingsLoading = ref(false)
const savingKey = ref('')

const announcements = ref([])
const annLoading = ref(false)
const annDialogOpen = ref(false)
const submitting = ref(false)
const annForm = reactive({ title: '', content: '', priority: 'normal' })

const deleteDialogOpen = ref(false)
const deletingAnn = ref(null)
const deleting = ref(false)

const logs = ref([])
const logsLoading = ref(false)
const page = ref(1)
const total = ref(0)
const actionFilter = ref(null)

const systemInfo = ref(null)
const infoLoading = ref(false)

const priorityOptions = [
  { label: '一般', value: 'normal' },
  { label: '重要', value: 'important' },
  { label: '紧急', value: 'urgent' }
]

const actionOptions = [
  { label: '全部动作', value: null },
  { label: '登录', value: 'LOGIN' },
  { label: '读者注册', value: 'REGISTER' },
  { label: '修改密码', value: 'CHANGE_PASSWORD' },
  { label: '借出', value: 'CIRC_BORROW' },
  { label: '归还', value: 'CIRC_RETURN' },
  { label: '新建书目', value: 'CREATE_BOOK' },
  { label: '注销书目', value: 'DELETE_BOOK' },
  { label: '新建读者', value: 'CREATE_READER' },
  { label: '重置密码', value: 'RESET_PWD' },
  { label: '罚金结算', value: 'FINE_SETTLE' },
  { label: '更新设置', value: 'UPDATE_SETTING' }
]

const metaOf = key => settingMeta[key] || { label: key, desc: '' }
const isBoolValue = value => ['true', 'false'].includes(String(value).toLowerCase())
const isTrue = value => String(value).toLowerCase() === 'true'

// Select 组件回传的是整个 option 对象，这里转换成后端需要的字符串值
const prioritySelected = computed({
  get: () => priorityOptions.find(o => o.value === annForm.priority) || priorityOptions[0],
  set: option => { annForm.priority = option?.value || 'normal' }
})

const actionSelected = computed({
  get: () => actionOptions.find(o => o.value === actionFilter.value) || actionOptions[0],
  set: option => {
    actionFilter.value = option?.value ?? null
    page.value = 1
    loadLogs()
  }
})

const infoRows = computed(() => {
  const info = systemInfo.value
  if (!info) return []
  const topLabels = {
    app_name: '应用名称',
    version: '版本号',
    database: '数据库类型',
    covers_dir: '封面存储目录',
    token_expire_minutes: '令牌有效期（分钟）'
  }
  const ruleLabels = {
    default_borrow_days: '默认借期（天）',
    max_renew_times: '最大续借次数',
    renew_days: '续借天数',
    daily_fine_rate: '日罚金（元/天）',
    max_borrow_books: '最大可借册数',
    reservation_expire_days: '预约保留天数',
    due_reminder_days: '到期提醒提前天数'
  }
  const rows = []
  Object.entries(info).forEach(([key, value]) => {
    if (key === 'rules' && value && typeof value === 'object') {
      Object.entries(value).forEach(([ruleKey, ruleValue]) => {
        rows.push({ label: ruleLabels[ruleKey] || ruleKey, value: ruleValue })
      })
      return
    }
    rows.push({ label: topLabels[key] || key, value })
  })
  return rows
})

const priorityLabel = priority => ({ urgent: '紧急', important: '重要', normal: '一般' }[priority] || '一般')
const priorityVariant = priority => (priority === 'urgent' ? 'danger' : priority === 'important' ? 'warning' : 'default')

const formatDateTime = value => (value ? new Date(value).toLocaleString('zh-CN') : '-')

const loadSettings = async () => {
  settingsLoading.value = true
  try {
    const { data } = await systemApi.getSettings()
    settings.value = data.map(item => ({
      key: item.setting_key,
      value: item.setting_value,
      description: item.description,
      draft: item.setting_value
    }))
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '加载系统设置失败')
  } finally {
    settingsLoading.value = false
  }
}

const persistSetting = async (item, value) => {
  savingKey.value = item.key
  try {
    await systemApi.updateSetting(item.key, value)
    window.$toast?.success('设置已更新')
    await loadSettings()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '设置更新失败')
  } finally {
    savingKey.value = ''
  }
}

const saveSetting = item => persistSetting(item, String(item.draft ?? '').trim())

const toggleBool = (item, next) => persistSetting(item, next ? 'true' : 'false')

const loadAnnouncements = async () => {
  annLoading.value = true
  try {
    const { data } = await announcementsApi.getActive()
    announcements.value = data
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '加载公告失败')
  } finally {
    annLoading.value = false
  }
}

const openAnnDialog = () => {
  Object.assign(annForm, { title: '', content: '', priority: 'normal' })
  annDialogOpen.value = true
}

const submitAnnouncement = async () => {
  submitting.value = true
  try {
    await announcementsApi.create({ ...annForm })
    window.$toast?.success('公告已发布')
    annDialogOpen.value = false
    loadAnnouncements()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '公告发布失败')
  } finally {
    submitting.value = false
  }
}

const askDelete = ann => {
  deletingAnn.value = ann
  deleteDialogOpen.value = true
}

const confirmDelete = async () => {
  deleting.value = true
  try {
    await announcementsApi.delete(deletingAnn.value.id)
    window.$toast?.success('公告已删除')
    deleteDialogOpen.value = false
    loadAnnouncements()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '删除公告失败')
  } finally {
    deleting.value = false
  }
}

// 多取一条用于判断是否还有下一页，Pagination 需要总量的近似值
const loadLogs = async () => {
  logsLoading.value = true
  try {
    const skip = (page.value - 1) * PAGE_SIZE
    const params = { skip, limit: PAGE_SIZE + 1 }
    if (actionFilter.value) params.action = actionFilter.value

    const { data } = await systemApi.getAuditLogs(params)
    const hasMore = data.length > PAGE_SIZE
    logs.value = data.slice(0, PAGE_SIZE)
    total.value = skip + logs.value.length + (hasMore ? 1 : 0)
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '加载审计日志失败')
  } finally {
    logsLoading.value = false
  }
}

const changePage = next => {
  page.value = next
  loadLogs()
}

const loadInfo = async () => {
  infoLoading.value = true
  try {
    const { data } = await systemApi.getInfo()
    systemInfo.value = data
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '加载系统信息失败')
  } finally {
    infoLoading.value = false
  }
}

const loadAll = async () => {
  refreshing.value = true
  await Promise.all([
    loadSettings(),
    loadAnnouncements(),
    loadLogs(),
    loadInfo()
  ])
  refreshing.value = false
}

onMounted(() => {
  loadAll()
})
</script>
