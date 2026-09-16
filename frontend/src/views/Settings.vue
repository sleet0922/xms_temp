<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">系统设置</h1>
        <p class="text-gray-600 mt-1">借阅规则与系统配置</p>
      </div>

      <Card padding="normal">
        <Tabs :tabs="['借阅规则', '馆内公告', '审计日志']" v-model="activeTab">
          <template #panel-0>
            <div class="space-y-6">
              <div v-for="setting in settings" :key="setting.key" class="flex items-center justify-between py-3 border-b border-gray-200 last:border-0">
                <div>
                  <div class="font-medium text-gray-900">{{ getSettingLabel(setting.key) }}</div>
                  <div class="text-sm text-gray-500">{{ getSettingDescription(setting.key) }}</div>
                </div>
                <Input
                  v-model="setting.value"
                  type="number"
                  class="w-24"
                  @blur="updateSetting(setting.key, setting.value)"
                />
              </div>
            </div>
          </template>

          <template #panel-1>
            <div class="space-y-4">
              <div v-if="userStore.isLibrarian" class="flex justify-end">
                <Button variant="primary" @click="showAddAnnDialog = true" :prepend-icon="PlusIcon">
                  发布公告
                </Button>
              </div>

              <div class="space-y-3">
                <Card v-for="ann in announcements" :key="ann.id" padding="small">
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-2 mb-2">
                        <Badge :variant="ann.priority === 'urgent' ? 'danger' : ann.priority === 'important' ? 'warning' : 'default'" size="small">
                          {{ getPriorityLabel(ann.priority) }}
                        </Badge>
                        <span class="text-xs text-gray-500">{{ formatDate(ann.created_at) }}</span>
                      </div>
                      <div class="font-medium text-gray-900 mb-1">{{ ann.title }}</div>
                      <div class="text-sm text-gray-600">{{ ann.content }}</div>
                    </div>
                    <Button
                      v-if="userStore.isAdmin"
                      size="small"
                      variant="ghost"
                      @click="deleteAnnouncement(ann.id)"
                    >
                      删除
                    </Button>
                  </div>
                </Card>
              </div>
            </div>
          </template>

          <template #panel-2>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-gray-50">
                  <tr class="border-b border-gray-200">
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">时间</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">用户</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">操作</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">对象</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  <tr v-for="log in auditLogs" :key="log.id" class="hover:bg-gray-50 transition-colors">
                    <td class="px-4 py-3 text-sm text-gray-600">{{ formatDateTime(log.created_at) }}</td>
                    <td class="px-4 py-3 text-sm text-gray-900">{{ log.user_id }}</td>
                    <td class="px-4 py-3">
                      <Badge size="small" class="font-mono text-xs">{{ log.action }}</Badge>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">{{ log.target_type }} #{{ log.target_id }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </Tabs>
      </Card>

      <!-- Add Announcement Dialog -->
      <Dialog v-model="showAddAnnDialog" title="发布公告" max-width="lg" persistent>
        <form @submit.prevent="handleAddAnnouncement" class="space-y-4">
          <Input v-model="annForm.title" label="标题" required />
          <Textarea v-model="annForm.content" label="内容" rows="4" required />
          <Select
            v-model="annForm.priority"
            :options="priorityOptions"
            label="优先级"
            required
          />
          <div class="flex justify-end gap-3">
            <Button variant="outline" @click="showAddAnnDialog = false">取消</Button>
            <Button type="submit" variant="primary" :loading="loading">发布</Button>
          </div>
        </form>
      </Dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { PlusIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Select from '@/components/ui/Select.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Tabs from '@/components/ui/Tabs.vue'
import { settingsApi, announcementsApi } from '@/api'

const userStore = useUserStore()

const activeTab = ref(0)
const settings = ref([])
const announcements = ref([])
const auditLogs = ref([])
const loading = ref(false)

const showAddAnnDialog = ref(false)
const annForm = reactive({
  title: '',
  content: '',
  priority: 'normal'
})

const priorityOptions = [
  { label: '一般', value: 'normal' },
  { label: '重要', value: 'important' },
  { label: '紧急', value: 'urgent' }
]

const settingLabels = {
  default_borrow_days: '默认借期（天）',
  max_renew_times: '最大续借次数',
  overdue_fine_per_day: '逾期罚金（元/天）',
  max_borrow_limit: '默认借阅额度'
}

const settingDescriptions = {
  default_borrow_days: '新借图书的默认借阅天数',
  max_renew_times: '每本书可续借的最大次数',
  overdue_fine_per_day: '图书逾期每天产生的罚金',
  max_borrow_limit: '新读者的默认可借图书数量'
}

const getSettingLabel = (key) => settingLabels[key] || key
const getSettingDescription = (key) => settingDescriptions[key] || ''

const getPriorityLabel = (priority) => {
  const labels = { urgent: '紧急', important: '重要', normal: '一般' }
  return labels[priority] || priority
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadSettings = async () => {
  try {
    const response = await settingsApi.getAll()
    settings.value = response.data.map(s => ({
      key: s.setting_key,
      value: s.setting_value
    }))
  } catch (err) {
    window.$toast?.error('加载设置失败')
  }
}

const updateSetting = async (key, value) => {
  try {
    await settingsApi.update(key, value)
    window.$toast?.success('设置已更新')
  } catch (err) {
    window.$toast?.error('更新失败')
  }
}

const loadAnnouncements = async () => {
  try {
    const response = await announcementsApi.getActive()
    announcements.value = response.data
  } catch (err) {
    window.$toast?.error('加载公告失败')
  }
}

const handleAddAnnouncement = async () => {
  loading.value = true
  try {
    await announcementsApi.create(annForm)
    window.$toast?.success('公告已发布')
    showAddAnnDialog.value = false
    Object.assign(annForm, { title: '', content: '', priority: 'normal' })
    loadAnnouncements()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '发布失败')
  } finally {
    loading.value = false
  }
}

const deleteAnnouncement = async (id) => {
  if (!confirm('确认删除该公告？')) return
  try {
    await announcementsApi.delete(id)
    window.$toast?.success('公告已删除')
    loadAnnouncements()
  } catch (err) {
    window.$toast?.error('删除失败')
  }
}

onMounted(() => {
  loadSettings()
  loadAnnouncements()
})
</script>
