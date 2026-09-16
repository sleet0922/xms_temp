<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">读者档案管理</h1>
          <p class="text-gray-600 mt-1">借阅证发放与读者信息维护</p>
        </div>
        <Button v-if="userStore.isLibrarian" variant="primary" @click="showAddDialog = true" :prepend-icon="PlusIcon">
          新发借阅证
        </Button>
      </div>

      <!-- Filters -->
      <Card padding="normal" class="mb-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input v-model="search" placeholder="搜索姓名、卡号" :prepend-icon="MagnifyingGlassIcon" />
          <Select v-model="statusFilter" :options="statusOptions" placeholder="状态筛选" />
          <Select v-model="roleFilter" :options="roleOptions" placeholder="角色筛选" />
        </div>
      </Card>

      <!-- Readers Table -->
      <Card padding="none">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">姓名</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">卡号</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">角色</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">在借/额度</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="reader in readers" :key="reader.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ reader.full_name }}</td>
                <td class="px-4 py-3 text-sm text-gray-600 font-mono">{{ reader.card_number }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="reader.role === 'admin' ? 'danger' : reader.role === 'librarian' ? 'primary' : 'default'" size="small">
                    {{ getRoleLabel(reader.role) }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ reader.borrowed_count }}/{{ reader.max_borrow_limit }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="reader.status === 'active' ? 'success' : 'danger'" size="small">
                    {{ reader.status === 'active' ? '正常' : '冻结' }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right space-x-2">
                  <Button size="small" variant="ghost" @click="toggleStatus(reader)">
                    {{ reader.status === 'active' ? '冻结' : '解冻' }}
                  </Button>
                  <Button size="small" variant="ghost" @click="resetPassword(reader)">重置密码</Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Add Reader Dialog -->
      <Dialog v-model="showAddDialog" title="新发借阅证" max-width="lg" persistent>
        <form @submit.prevent="handleAddReader" class="space-y-4">
          <Input v-model="readerForm.username" label="用户名" required />
          <Input v-model="readerForm.full_name" label="真实姓名" required />
          <Input v-model="readerForm.email" label="邮箱" type="email" required />
          <Input v-model="readerForm.phone" label="联系电话" />
          <Select v-model="readerForm.role" :options="roleOptions" label="角色" required />
          <Input v-model.number="readerForm.max_borrow_limit" type="number" label="借阅额度" :min="1" required />
          <div class="flex justify-end gap-3">
            <Button variant="outline" @click="showAddDialog = false">取消</Button>
            <Button type="submit" variant="primary" :loading="loading">提交</Button>
          </div>
        </form>
      </Dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { MagnifyingGlassIcon, PlusIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import { readersApi } from '@/api'

const userStore = useUserStore()

const readers = ref([])
const search = ref('')
const statusFilter = ref(null)
const roleFilter = ref(null)
const loading = ref(false)
const showAddDialog = ref(false)

const readerForm = reactive({
  username: '',
  full_name: '',
  email: '',
  phone: '',
  role: 'reader',
  max_borrow_limit: 5
})

const statusOptions = [
  { label: '全部', value: null },
  { label: '正常', value: 'active' },
  { label: '冻结', value: 'frozen' }
]

const roleOptions = [
  { label: 'admin', value: 'admin' },
  { label: 'librarian', value: 'librarian' },
  { label: 'reader', value: 'reader' }
]

const getRoleLabel = (role) => {
  const labels = { admin: '管理员', librarian: '馆员', reader: '读者' }
  return labels[role] || role
}

const loadReaders = async () => {
  loading.value = true
  try {
    const params = {
      search: search.value,
      status_filter: statusFilter.value,
      role_filter: roleFilter.value
    }
    const response = await readersApi.getList(params)
    readers.value = response.data
  } catch (err) {
    window.$toast?.error('加载读者列表失败')
  } finally {
    loading.value = false
  }
}

const toggleStatus = async (reader) => {
  try {
    const newStatus = reader.status === 'active' ? 'frozen' : 'active'
    await readersApi.update(reader.id, { status: newStatus })
    window.$toast?.success(`已${newStatus === 'active' ? '解冻' : '冻结'}`)
    loadReaders()
  } catch (err) {
    window.$toast?.error('操作失败')
  }
}

const resetPassword = async (reader) => {
  if (!confirm(`确认重置 ${reader.full_name} 的密码？`)) return
  try {
    await readersApi.resetPassword(reader.id)
    window.$toast?.success('密码已重置为 123456')
  } catch (err) {
    window.$toast?.error('重置失败')
  }
}

const handleAddReader = async () => {
  loading.value = true
  try {
    await readersApi.create(readerForm)
    window.$toast?.success('借阅证发放成功')
    showAddDialog.value = false
    Object.assign(readerForm, { username: '', full_name: '', email: '', phone: '', role: 'reader', max_borrow_limit: 5 })
    loadReaders()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '发放失败')
  } finally {
    loading.value = false
  }
}

watch([search, statusFilter, roleFilter], () => {
  loadReaders()
})

onMounted(() => {
  loadReaders()
})
</script>
