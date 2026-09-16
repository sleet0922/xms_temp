<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">书目大厅</h1>
          <p class="text-gray-600 mt-1">馆藏图书检索与管理</p>
        </div>
        <div class="flex gap-3">
          <Button variant="outline" @click="exportBooks" :prepend-icon="DocumentTextIcon">导出</Button>
          <Button v-if="userStore.isLibrarian" variant="primary" @click="showAddDialog = true" :prepend-icon="PlusIcon">
            新增图书
          </Button>
        </div>
      </div>

      <!-- Filters -->
      <Card padding="normal" class="mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Input v-model="search" placeholder="搜索书名、作者、ISBN" :prepend-icon="MagnifyingGlassIcon" />
          <Select v-model="selectedCategory" :options="categories" label="分类筛选" placeholder="全部分类" item-title="name" item-value="id" />
          <Select v-model="sortBy" :options="sortOptions" label="排序" item-title="label" item-value="value" />
          <div class="flex items-end">
            <label class="flex items-center gap-2 text-sm text-gray-700">
              <Switch v-model="inStockOnly" />
              仅看有库存
            </label>
          </div>
        </div>
      </Card>

      <!-- View Toggle -->
      <div class="flex justify-between items-center mb-4">
        <div class="text-sm text-gray-600">共 {{ books.length }} 本图书</div>
        <div class="flex gap-2">
          <Button size="small" :variant="viewMode === 'grid' ? 'primary' : 'outline'" @click="viewMode = 'grid'">网格</Button>
          <Button size="small" :variant="viewMode === 'table' ? 'primary' : 'outline'" @click="viewMode = 'table'">表格</Button>
        </div>
      </div>

      <!-- Grid View -->
      <div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card v-for="book in books" :key="book.id" hover clickable padding="none" @click="viewBook(book)">
          <div class="h-48 bg-gray-100 flex items-center justify-center">
            <BookOpenIcon class="w-16 h-16 text-gray-400" />
          </div>
          <div class="p-4">
            <h3 class="font-semibold text-gray-900 mb-1 truncate">{{ book.title }}</h3>
            <p class="text-sm text-gray-600 mb-2 truncate">{{ book.author }}</p>
            <div class="flex items-center justify-between">
              <Badge :variant="book.available_copies > 0 ? 'success' : 'danger'" size="small">
                {{ book.available_copies }}/{{ book.total_copies }} 在架
              </Badge>
              <span class="text-xs text-gray-500">借 {{ book.borrow_count }} 次</span>
            </div>
          </div>
        </Card>
      </div>

      <!-- Table View -->
      <Card v-else padding="none">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">书名</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">作者</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">分类</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">库存</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">借阅次数</th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="book in books" :key="book.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ book.title }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ book.author }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ book.category?.name }}</td>
                <td class="px-4 py-3">
                  <Badge :variant="book.available_copies > 0 ? 'success' : 'danger'" size="small">
                    {{ book.available_copies }}/{{ book.total_copies }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ book.borrow_count }}</td>
                <td class="px-4 py-3 text-right">
                  <Button size="small" variant="ghost" @click="viewBook(book)">详情</Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <!-- Book Detail Dialog -->
      <Dialog v-model="showDetailDialog" title="图书详情" max-width="2xl">
        <div v-if="selectedBook" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div><span class="text-gray-600">书名：</span>{{ selectedBook.title }}</div>
            <div><span class="text-gray-600">作者：</span>{{ selectedBook.author }}</div>
            <div><span class="text-gray-600">ISBN：</span>{{ selectedBook.isbn }}</div>
            <div><span class="text-gray-600">分类：</span>{{ selectedBook.category?.name }}</div>
          </div>
          <div>
            <h4 class="font-semibold mb-2">单册清册</h4>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left">条形码</th>
                    <th class="px-3 py-2 text-left">状态</th>
                  </tr>
                </thead>
                <tbody class="divide-y">
                  <tr v-for="copy in selectedBook.copies" :key="copy.id">
                    <td class="px-3 py-2 font-mono text-xs">{{ copy.barcode }}</td>
                    <td class="px-3 py-2">
                      <Badge :variant="copy.status === 'available' ? 'success' : 'warning'" size="small">
                        {{ getCopyStatusLabel(copy.status) }}
                      </Badge>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Dialog>

      <!-- Add Book Dialog -->
      <Dialog v-model="showAddDialog" title="新增图书" max-width="lg" persistent>
        <form @submit.prevent="handleAddBook" class="space-y-4">
          <Input v-model="bookForm.title" label="书名" required />
          <Input v-model="bookForm.author" label="作者" required />
          <Input v-model="bookForm.isbn" label="ISBN" required />
          <Select v-model="bookForm.category_id" :options="categories" label="分类" item-title="name" item-value="id" required />
          <Input v-model.number="bookForm.copies_count" type="number" label="初始册数" :min="1" required />
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
import {
  BookOpenIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Switch from '@/components/ui/Switch.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import { booksApi, categoriesApi } from '@/api'

const userStore = useUserStore()

const books = ref([])
const categories = ref([])
const search = ref('')
const selectedCategory = ref(null)
const sortBy = ref('created_at')
const inStockOnly = ref(false)
const viewMode = ref('grid')
const loading = ref(false)

const showDetailDialog = ref(false)
const selectedBook = ref(null)
const showAddDialog = ref(false)

const bookForm = reactive({
  title: '',
  author: '',
  isbn: '',
  category_id: null,
  copies_count: 1
})

const sortOptions = [
  { label: '最新添加', value: 'created_at' },
  { label: '借阅次数', value: 'borrow_count' },
  { label: '书名', value: 'title' }
]

const getCopyStatusLabel = (status) => {
  const labels = {
    available: '在架',
    borrowed: '借出',
    reserved: '预约',
    maintenance: '维护',
    lost: '遗失'
  }
  return labels[status] || status
}

const loadBooks = async () => {
  loading.value = true
  try {
    const params = {
      search: search.value,
      category_id: selectedCategory.value,
      sort_by: sortBy.value,
      in_stock_only: inStockOnly.value
    }
    const response = await booksApi.getList(params)
    books.value = response.data
  } catch (err) {
    window.$toast?.error('加载图书失败')
  } finally {
    loading.value = false
  }
}

const viewBook = async (book) => {
  try {
    const response = await booksApi.getById(book.id)
    selectedBook.value = response.data
    showDetailDialog.value = true
  } catch (err) {
    window.$toast?.error('加载图书详情失败')
  }
}

const exportBooks = async () => {
  try {
    const response = await booksApi.export()
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'books.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (err) {
    window.$toast?.error('导出失败')
  }
}

const handleAddBook = async () => {
  loading.value = true
  try {
    await booksApi.create(bookForm)
    window.$toast?.success('图书添加成功')
    showAddDialog.value = false
    Object.assign(bookForm, { title: '', author: '', isbn: '', category_id: null, copies_count: 1 })
    loadBooks()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '添加失败')
  } finally {
    loading.value = false
  }
}

watch([search, selectedCategory, sortBy, inStockOnly], () => {
  loadBooks()
}, { debounce: 300 })

onMounted(async () => {
  const catResponse = await categoriesApi.getAll()
  categories.value = catResponse.data
  loadBooks()
})
</script>
