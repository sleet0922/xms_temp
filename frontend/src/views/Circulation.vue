<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">智慧借还服务台</h1>
        <p class="text-gray-600 mt-1">扫码快速借还图书</p>
      </div>

      <Card padding="normal">
        <Tabs :tabs="['借出图书', '归还图书']" v-model="activeTab">
          <template #panel-0>
            <div class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">读者借阅证号</label>
                <Input
                  v-model="borrowForm.cardNumber"
                  placeholder="扫描或输入借阅证号"
                  :prepend-icon="IdentificationIcon"
                  @keyup.enter="loadReader"
                />
                <div class="flex gap-2 mt-2">
                  <Badge
                    v-for="preset in presetCards"
                    :key="preset"
                    @click="borrowForm.cardNumber = preset"
                    class="cursor-pointer hover:opacity-80"
                    size="small"
                  >
                    {{ preset }}
                  </Badge>
                </div>
              </div>

              <Card v-if="reader" padding="small" class="bg-blue-50 border-blue-200">
                <div class="flex items-center gap-3">
                  <UserCircleIcon class="w-10 h-10 text-blue-600" />
                  <div>
                    <div class="font-semibold text-gray-900">{{ reader.full_name }}</div>
                    <div class="text-sm text-gray-600">
                      在借: {{ reader.borrowed_count }}/{{ reader.max_borrow_limit }} |
                      余额: ¥{{ reader.balance }}
                    </div>
                  </div>
                  <Badge :variant="reader.status === 'active' ? 'success' : 'danger'" class="ml-auto">
                    {{ reader.status === 'active' ? '正常' : '冻结' }}
                  </Badge>
                </div>
              </Card>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">图书条形码</label>
                <Input
                  v-model="borrowForm.barcode"
                  placeholder="扫描图书条形码"
                  :prepend-icon="QrCodeIcon"
                  @keyup.enter="handleBorrow"
                  :disabled="!reader"
                />
              </div>

              <Button
                @click="handleBorrow"
                variant="primary"
                size="large"
                block
                :disabled="!reader || !borrowForm.barcode"
                :loading="borrowLoading"
              >
                确认借出
              </Button>

              <div v-if="borrowSession.length > 0" class="mt-6">
                <h3 class="font-semibold mb-3">本次已借 {{ borrowSession.length }} 本</h3>
                <div class="space-y-2">
                  <Card
                    v-for="(item, index) in borrowSession"
                    :key="index"
                    padding="small"
                    class="flex items-center justify-between"
                  >
                    <span class="text-sm">{{ item.book?.title }}</span>
                    <Badge variant="success" size="small">已借出</Badge>
                  </Card>
                </div>
              </div>
            </div>
          </template>

          <template #panel-1>
            <div class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">图书条形码</label>
                <Input
                  v-model="returnForm.barcode"
                  placeholder="扫描图书条形码"
                  :prepend-icon="QrCodeIcon"
                  @keyup.enter="handleReturn"
                />
              </div>

              <Button
                @click="handleReturn"
                variant="primary"
                size="large"
                block
                :disabled="!returnForm.barcode"
                :loading="returnLoading"
              >
                确认归还
              </Button>

              <div v-if="returnSession.length > 0" class="mt-6">
                <h3 class="font-semibold mb-3">本次已还 {{ returnSession.length }} 本</h3>
                <div class="space-y-2">
                  <Card
                    v-for="(item, index) in returnSession"
                    :key="index"
                    padding="small"
                    class="flex items-center justify-between"
                  >
                    <div>
                      <div class="text-sm font-medium">{{ item.book?.title }}</div>
                      <div v-if="item.fine" class="text-xs text-red-600">逾期罚金: ¥{{ item.fine }}</div>
                    </div>
                    <Badge variant="success" size="small">已归还</Badge>
                  </Card>
                </div>
              </div>
            </div>
          </template>
        </Tabs>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import {
  IdentificationIcon,
  QrCodeIcon,
  UserCircleIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Badge from '@/components/ui/Badge.vue'
import Tabs from '@/components/ui/Tabs.vue'
import { circulationApi, readersApi } from '@/api'

const activeTab = ref(0)

const borrowForm = reactive({
  cardNumber: '',
  barcode: ''
})

const returnForm = reactive({
  barcode: ''
})

const reader = ref(null)
const borrowLoading = ref(false)
const returnLoading = ref(false)
const borrowSession = ref([])
const returnSession = ref([])

const presetCards = ['CARD-202601101', 'CARD-202601102', 'CARD-202601103']

const loadReader = async () => {
  try {
    const response = await readersApi.getList({ search: borrowForm.cardNumber })
    const found = response.data.find(r => r.card_number === borrowForm.cardNumber)
    if (found) {
      reader.value = found
      window.$toast?.success(`读者 ${found.full_name} 已加载`)
    } else {
      window.$toast?.error('未找到该借阅证')
    }
  } catch (err) {
    window.$toast?.error('加载读者信息失败')
  }
}

const handleBorrow = async () => {
  borrowLoading.value = true
  try {
    const response = await circulationApi.borrow(borrowForm.cardNumber, borrowForm.barcode)
    borrowSession.value.push(response.data)
    window.$toast?.success('借出成功')
    borrowForm.barcode = ''
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '借出失败')
  } finally {
    borrowLoading.value = false
  }
}

const handleReturn = async () => {
  returnLoading.value = true
  try {
    const response = await circulationApi.return(returnForm.barcode)
    returnSession.value.push(response.data)
    window.$toast?.success('归还成功')
    returnForm.barcode = ''
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '归还失败')
  } finally {
    returnLoading.value = false
  }
}
</script>
