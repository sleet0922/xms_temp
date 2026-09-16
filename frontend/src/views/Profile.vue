<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <!-- Virtual Library Card -->
      <Card padding="none" class="mb-6 overflow-hidden bg-gradient-to-br from-blue-600 to-blue-700 text-white">
        <div class="p-6">
          <div class="flex items-start justify-between mb-4">
            <div>
              <div class="text-sm opacity-90 mb-1">未来智慧云图书馆</div>
              <div class="text-2xl font-bold">电子借阅证</div>
            </div>
            <Badge variant="primary" class="bg-white/20 text-white border-white/30">
              {{ roleLabel }}
            </Badge>
          </div>

          <div class="space-y-3 mb-6">
            <div class="flex items-center gap-3">
              <UserCircleIcon class="w-5 h-5 opacity-80" />
              <div>
                <div class="text-xs opacity-80">持证人</div>
                <div class="font-semibold">{{ user?.full_name || user?.username }}</div>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <IdentificationIcon class="w-5 h-5 opacity-80" />
              <div>
                <div class="text-xs opacity-80">证件号码</div>
                <div class="font-mono font-semibold tracking-wider">{{ user?.card_number }}</div>
              </div>
            </div>
          </div>

          <!-- Barcode decoration -->
          <div class="flex gap-0.5 opacity-30">
            <div v-for="i in 40" :key="i" class="w-1 h-12 bg-white" :class="{ 'w-0.5': i % 3 === 0 }"></div>
          </div>
        </div>
      </Card>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card hover>
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 mb-1">借阅额度</div>
              <div class="text-2xl font-bold text-gray-900">{{ user?.borrowed_count || 0 }} / {{ user?.max_borrow_limit || 5 }}</div>
            </div>
            <div class="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center">
              <BookOpenIcon class="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div class="mt-3">
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-blue-600 h-2 rounded-full transition-all duration-200"
                :style="{ width: `${((user?.borrowed_count || 0) / (user?.max_borrow_limit || 5)) * 100}%` }"
              ></div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 mb-1">账户余额</div>
              <div class="text-2xl font-bold text-gray-900">¥{{ parseFloat(user?.balance || 0).toFixed(2) }}</div>
            </div>
            <div class="w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center">
              <BanknotesIcon class="w-6 h-6 text-green-600" />
            </div>
          </div>
        </Card>

        <Card hover>
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 mb-1">账户状态</div>
              <Badge :variant="user?.status === 'active' ? 'success' : 'danger'" class="mt-1">
                {{ user?.status === 'active' ? '正常' : '冻结' }}
              </Badge>
            </div>
            <div class="w-12 h-12 rounded-lg bg-gray-50 flex items-center justify-center">
              <CheckCircleIcon class="w-6 h-6 text-gray-600" />
            </div>
          </div>
        </Card>
      </div>

      <!-- Borrowed Books -->
      <Card padding="normal" class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-gray-900">我的在借图书</h3>
          <Badge variant="primary">{{ borrows.length }} 本</Badge>
        </div>

        <div v-if="loading" class="text-center py-8 text-gray-500">
          加载中...
        </div>

        <div v-else-if="borrows.length === 0" class="text-center py-8 text-gray-500">
          暂无在借图书
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr class="border-b border-gray-200">
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">书名</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">借出日期</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">应还日期</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="borrow in borrows" :key="borrow.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ borrow.book?.title }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(borrow.borrow_date) }}</td>
                <td class="px-4 py-3 text-sm" :class="isOverdue(borrow.due_date) ? 'text-red-600 font-medium' : 'text-gray-600'">
                  {{ formatDate(borrow.due_date) }}
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="isOverdue(borrow.due_date) ? 'danger' : 'success'">
                    {{ isOverdue(borrow.due_date) ? '已逾期' : '正常' }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right">
                  <Button
                    size="small"
                    :variant="isOverdue(borrow.due_date) ? 'outline' : 'primary'"
                    :disabled="isOverdue(borrow.due_date)"
                    @click="handleRenew(borrow.id)"
                  >
                    续借
                  </Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Change Password -->
      <Card padding="normal">
        <h3 class="text-lg font-bold text-gray-900 mb-4">修改密码</h3>

        <form @submit.prevent="handleChangePassword" class="space-y-4">
          <Input
            v-model="passwordForm.old_password"
            label="当前密码"
            type="password"
            :prepend-icon="LockClosedIcon"
            :error="passwordErrors.old_password"
            required
          />

          <Input
            v-model="passwordForm.new_password"
            label="新密码"
            type="password"
            :prepend-icon="LockClosedIcon"
            hint="至少 6 位字符"
            :error="passwordErrors.new_password"
            required
          />

          <Alert v-if="passwordError" variant="error" :message="passwordError" class="mt-4" />
          <Alert v-if="passwordSuccess" variant="success" :message="passwordSuccess" class="mt-4" />

          <div class="flex justify-end">
            <Button type="submit" variant="primary" :loading="passwordLoading">
              确认修改
            </Button>
          </div>
        </form>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import {
  UserCircleIcon,
  IdentificationIcon,
  BookOpenIcon,
  BanknotesIcon,
  CheckCircleIcon,
  LockClosedIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Alert from '@/components/ui/Alert.vue'
import { borrowsApi, authApi } from '@/api'

const userStore = useUserStore()
const user = computed(() => userStore.user)

const roleLabels = {
  admin: '系统管理员',
  librarian: '服务台馆员',
  reader: '普通读者'
}

const roleLabel = computed(() => roleLabels[user.value?.role] || '读者')

const borrows = ref([])
const loading = ref(false)

const passwordForm = reactive({
  old_password: '',
  new_password: ''
})

const passwordErrors = reactive({
  old_password: '',
  new_password: ''
})

const passwordLoading = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const isOverdue = (dueDate) => {
  if (!dueDate) return false
  return new Date(dueDate) < new Date()
}

const loadMyBorrows = async () => {
  loading.value = true
  try {
    const response = await borrowsApi.getMyBorrows()
    borrows.value = response.data.filter(b => b.status === 'borrowed' || b.status === 'overdue')
  } catch (err) {
    console.error('Failed to load borrows:', err)
  } finally {
    loading.value = false
  }
}

const handleRenew = async (borrowId) => {
  try {
    await borrowsApi.renewBorrow(borrowId)
    window.$toast?.success('续借成功')
    loadMyBorrows()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '续借失败')
  }
}

const handleChangePassword = async () => {
  passwordErrors.old_password = ''
  passwordErrors.new_password = ''
  passwordError.value = ''
  passwordSuccess.value = ''

  if (passwordForm.new_password.length < 6) {
    passwordErrors.new_password = '新密码至少 6 位字符'
    return
  }

  passwordLoading.value = true
  try {
    await authApi.changePassword(passwordForm.old_password, passwordForm.new_password)
    passwordSuccess.value = '密码修改成功'
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } catch (err) {
    passwordError.value = err.response?.data?.detail || '密码修改失败'
  } finally {
    passwordLoading.value = false
  }
}

onMounted(() => {
  loadMyBorrows()
})
</script>
