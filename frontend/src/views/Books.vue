<template>
  <div class="neo-page p-6 lg:p-8 max-w-7xl mx-auto">
    <PageHeader title="书目大厅" subtitle="电子馆藏检索、筛选与编目管理">
      <template #actions>
        <Button variant="outline" :prepend-icon="DocumentArrowDownIcon" @click="exportBooks">导出</Button>
        <Button v-if="userStore.isLibrarian" variant="primary" :prepend-icon="PlusIcon" @click="showAddDialog = true">
          新增图书
        </Button>
      </template>
    </PageHeader>

    <!-- 馆藏概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
      <StatCard label="馆藏总量" :value="facets.total || 0" hint="当前检索库全部书目" :icon="BookOpenIcon" tone="primary" />
      <StatCard label="语种分布" :value="facets.languages?.length || 0" :hint="languageHint" :icon="LanguageIcon" tone="neutral" />
      <StatCard label="电子资源格式" :value="facets.formats?.length || 0" :hint="formatHint" :icon="DocumentIcon" tone="success" />
    </div>

    <!-- 检索区 -->
    <Card class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Input
          v-model="search"
          label="关键词"
          placeholder="书名、作者、ISBN、出版社、简介"
          :prepend-icon="MagnifyingGlassIcon"
        />
        <Select v-model="selectedCategory" :options="categoryOptions" label="分类" placeholder="全部分类" item-title="label" item-value="value" />
        <Select v-model="language" :options="languageOptions" label="语种" placeholder="全部语种" item-title="label" item-value="value" />
        <Select v-model="format" :options="formatOptions" label="格式" placeholder="全部格式" item-title="label" item-value="value" />
        <Select v-model="sortBy" :options="sortOptions" label="排序" item-title="label" item-value="value" />
        <div class="flex items-end gap-6">
          <label class="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
            <Switch v-model="inStockOnly" label="仅看有库存" />
            仅看有库存
          </label>
        </div>
        <div class="flex items-end">
          <Button variant="outline" :prepend-icon="ArrowPathIcon" @click="resetFilters">重置筛选</Button>
        </div>
      </div>

      <!-- 快捷筛选标签 -->
      <div v-if="formatChips.length || languageChips.length" class="flex flex-wrap items-center gap-2 mt-5 pt-5 border-t border-gray-200">
        <span class="text-xs font-medium text-gray-500 mr-1">快捷筛选</span>
        <button
          type="button"
          v-for="chip in formatChips"
          :key="`fmt-${chip.value}`"
          class="px-3 py-1 rounded-lg text-xs font-medium transition-all duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
          :class="format === chip.value ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
          @click="format = format === chip.value ? null : chip.value"
        >
          {{ chip.value }} · {{ chip.count }}
        </button>
        <button
          type="button"
          v-for="chip in languageChips"
          :key="`lang-${chip.value}`"
          class="px-3 py-1 rounded-lg text-xs font-medium transition-all duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
          :class="language === chip.value ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
          @click="language = language === chip.value ? null : chip.value"
        >
          {{ chip.value }} · {{ chip.count }}
        </button>
      </div>
    </Card>

    <!-- 结果工具条 -->
    <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
      <div class="text-sm text-gray-600">
        第 {{ page }} 页 · 本页 {{ books.length }} 本
        <span v-if="loading" class="text-gray-400 ml-2">加载中…</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="flex rounded-lg border border-gray-300 overflow-hidden">
          <button
            type="button"
            class="px-3 py-1.5 text-sm font-medium transition-all duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
            :class="viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'"
            @click="viewMode = 'grid'"
          >
            网格
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-sm font-medium transition-all duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
            :class="viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'"
            @click="viewMode = 'table'"
          >
            表格
          </button>
        </div>
      </div>
    </div>

    <!-- 网格视图 -->
    <div v-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card
        v-for="book in books"
        :key="book.id"
        padding="none"
        hover
        clickable
        class="overflow-hidden"
        @click="goDetail(book)"
      >
        <BookCover :book="book" ratio="3/4" />
        <div class="p-6">
          <h3 class="font-semibold tracking-tight text-gray-900 truncate">{{ book.title }}</h3>
          <p class="text-sm text-gray-600 truncate mt-0.5">{{ book.author }}</p>

          <div class="flex items-center gap-2 mt-3 flex-wrap">
            <Badge v-if="book.format" variant="primary" size="small">{{ book.format }}</Badge>
            <Badge v-if="book.language" variant="secondary" size="small">{{ book.language }}</Badge>
          </div>

          <div class="mt-3">
            <RatingStars :model-value="Number(book.rating || 0)" :count="book.rating_count || 0" size="small" />
          </div>

          <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
            <Badge :variant="book.available_copies > 0 ? 'success' : 'default'" size="small">
              {{ book.available_copies > 0 ? `${book.available_copies}/${book.total_copies} 在架` : '暂无可借' }}
            </Badge>
            <span class="text-xs text-gray-500">借阅 {{ book.borrow_count }} 次</span>
          </div>
        </div>
      </Card>
    </div>

    <!-- 表格视图 -->
    <Card v-else padding="none">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">书名</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">作者</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">分类</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">格式</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">评分</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">库存</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">借阅次数</th>
              <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="book in books" :key="book.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 text-sm font-medium text-gray-900 max-w-xs truncate">{{ book.title }}</td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ book.author }}</td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ book.category?.name || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ book.format || '-' }}</td>
              <td class="px-4 py-3">
                <RatingStars :model-value="Number(book.rating || 0)" size="small" />
              </td>
              <td class="px-4 py-3">
                <Badge :variant="book.available_copies > 0 ? 'success' : 'default'" size="small">
                  {{ book.available_copies }}/{{ book.total_copies }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-sm text-gray-600">{{ book.borrow_count }}</td>
              <td class="px-4 py-3 text-right">
                <Button size="small" variant="ghost" @click="goDetail(book)">详情</Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState v-if="!loading && !books.length" title="没有匹配的书目" description="试试更换关键词，或重置筛选条件" :icon="MagnifyingGlassIcon" />
    </Card>

    <!-- 分页（后端逐页取数，按是否有下一页控制） -->
    <div v-if="books.length || page > 1" class="flex items-center justify-between gap-4 mt-6">
      <div class="text-sm text-gray-500">第 {{ page }} 页</div>
      <div class="flex items-center gap-2">
        <Button size="small" variant="outline" :disabled="page <= 1 || loading" @click="page--">上一页</Button>
        <Button size="small" variant="outline" :disabled="!hasNext || loading" @click="page++">下一页</Button>
      </div>
    </div>

    <!-- 新增图书 -->
    <Dialog v-model="showAddDialog" title="新增图书" max-width="lg" persistent>
      <form class="space-y-4" @submit.prevent="handleAddBook">
        <Input v-model="bookForm.title" label="书名" required />
        <Input v-model="bookForm.author" label="作者" required />
        <Input v-model="bookForm.isbn" label="ISBN" hint="电子资源可留空" />
        <div class="grid grid-cols-2 gap-4">
          <Select v-model="bookForm.category_id" :options="categoryOptions" label="分类" item-title="label" item-value="value" />
          <Input v-model.number="bookForm.copies_count" type="number" label="初始册数" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <Input v-model="bookForm.language" label="语种" placeholder="中文 / 英文" />
          <Input v-model="bookForm.format" label="格式" placeholder="EPUB / PDF" />
        </div>
        <Textarea v-model="bookForm.description" label="内容简介" :rows="3" />
      </form>
      <template #footer>
        <Button variant="outline" @click="showAddDialog = false">取消</Button>
        <Button variant="primary" :loading="submitting" @click="handleAddBook">提交</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowPathIcon,
  BookOpenIcon,
  DocumentArrowDownIcon,
  DocumentIcon,
  LanguageIcon,
  MagnifyingGlassIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'
import { useUserStore } from '@/stores/user'
import { booksApi } from '@/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Switch from '@/components/ui/Switch.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import RatingStars from '@/components/ui/RatingStars.vue'
import BookCover from '@/components/ui/BookCover.vue'

const router = useRouter()
const userStore = useUserStore()

const PAGE_SIZE = 24

const books = ref([])
const facets = ref({})
const search = ref('')
const selectedCategory = ref(null)
const language = ref(null)
const format = ref(null)
const sortBy = ref('created_at')
const inStockOnly = ref(false)
const viewMode = ref('grid')
const loading = ref(false)
const page = ref(1)
const hasNext = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)

const bookForm = reactive({
  title: '',
  author: '',
  isbn: '',
  category_id: null,
  language: '',
  format: '',
  description: '',
  copies_count: 3
})

const sortOptions = [
  { label: '最新上架', value: 'created_at' },
  { label: '借阅热度', value: 'borrow_count' },
  { label: '读者评分', value: 'rating' },
  { label: '浏览量', value: 'views' },
  { label: '书名排序', value: 'title' },
  { label: '价格', value: 'price' }
]

const categoryOptions = computed(() => (facets.value.categories || []).map(c => ({ label: c.label, value: c.value })))
const languageOptions = computed(() => (facets.value.languages || []).map(l => ({ label: l.value, value: l.value })))
const formatOptions = computed(() => (facets.value.formats || []).map(f => ({ label: f.value, value: f.value })))
const formatChips = computed(() => (facets.value.formats || []).slice(0, 6))
const languageChips = computed(() => (facets.value.languages || []).slice(0, 4))
const languageHint = computed(() => languageChips.value.map(l => `${l.value} ${l.count}`).join(' · ') || '暂无数据')
const formatHint = computed(() => formatChips.value.map(f => `${f.value} ${f.count}`).join(' · ') || '暂无数据')

async function loadBooks() {
  loading.value = true
  try {
    const params = {
      search: search.value || undefined,
      category_id: selectedCategory.value || undefined,
      language: language.value || undefined,
      format: format.value || undefined,
      sort_by: sortBy.value,
      in_stock_only: inStockOnly.value || undefined,
      skip: (page.value - 1) * PAGE_SIZE,
      // 多取一条用于判断是否还有下一页
      limit: PAGE_SIZE + 1
    }
    const { data } = await booksApi.getList(params)
    hasNext.value = data.length > PAGE_SIZE
    books.value = data.slice(0, PAGE_SIZE)
  } catch (err) {
    window.$toast?.error('加载图书失败')
  } finally {
    loading.value = false
  }
}

async function loadFacets() {
  try {
    const { data } = await booksApi.getFacets()
    facets.value = data
  } catch (err) {
    console.error('加载筛选项失败', err)
  }
}

function resetFilters() {
  search.value = ''
  selectedCategory.value = null
  language.value = null
  format.value = null
  sortBy.value = 'created_at'
  inStockOnly.value = false
}

function goDetail(book) {
  router.push(`/books/${book.id}`)
}

async function exportBooks() {
  try {
    const { data } = await booksApi.export()
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'library_books.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    window.$toast?.error('导出失败')
  }
}

async function handleAddBook() {
  if (!bookForm.title || !bookForm.author) {
    window.$toast?.warning('书名与作者为必填项')
    return
  }
  submitting.value = true
  try {
    const { copies_count: copiesCount, ...payload } = bookForm
    await booksApi.create(payload, copiesCount || 1)
    window.$toast?.success('图书已录入')
    showAddDialog.value = false
    Object.assign(bookForm, { title: '', author: '', isbn: '', category_id: null, language: '', format: '', description: '', copies_count: 3 })
    loadFacets()
    loadBooks()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '录入失败')
  } finally {
    submitting.value = false
  }
}

// 关键词搜索防抖，避免每次按键都请求后端
let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadBooks()
  }, 350)
})

watch([selectedCategory, language, format, sortBy, inStockOnly], () => {
  page.value = 1
  loadBooks()
})

watch(page, loadBooks)

onMounted(() => {
  loadFacets()
  loadBooks()
})
</script>
