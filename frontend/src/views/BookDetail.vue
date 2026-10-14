<template>
  <div class="neo-page">
    <div class="mb-6 flex items-center gap-3">
      <Button variant="ghost" size="small" :prepend-icon="ArrowLeftIcon" @click="router.back()">返回</Button>
      <nav class="text-sm text-gray-500">
        <RouterLink :to="booksPath" class="hover:text-blue-600 transition-colors duration-150">{{ isAdminRoute ? '馆藏与书目' : '馆藏检索' }}</RouterLink>
        <span class="mx-1.5">/</span>
        <span class="text-gray-900 font-medium truncate">{{ book?.title || '图书详情' }}</span>
      </nav>
    </div>

    <div v-if="loading" class="py-16 text-center text-sm text-gray-500">加载中…</div>

    <EmptyState
      v-else-if="!book"
      :title="loadError.status === 404 ? '未找到该图书' : '图书详情加载失败'"
      :description="loadError.message"
      :icon="BookOpenIcon"
    >
      <template #action>
        <div class="flex flex-wrap items-center justify-center gap-3">
          <Button v-if="loadError.status !== 404" variant="outline" @click="loadBook">重试</Button>
          <Button variant="primary" @click="router.push(booksPath)">返回{{ isAdminRoute ? '馆藏与书目' : '馆藏检索' }}</Button>
        </div>
      </template>
    </EmptyState>

    <div v-else class="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-4 items-start">
      <!-- 左栏：封面与馆藏信息 -->
      <div class="space-y-6">
        <Card padding="none" class="overflow-hidden">
          <BookCover :book="book" ratio="3/4" />
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <Badge :variant="book.available_copies > 0 ? 'success' : 'warning'">
                {{ book.available_copies > 0 ? `在架 ${book.available_copies}/${book.total_copies}` : '暂无在架复本' }}
              </Badge>
              <span class="text-xs text-gray-500">借阅 {{ book.borrow_count }} 次</span>
            </div>

            <div class="flex flex-col gap-3">
              <Button
                v-if="book.available_copies > 0 && isAdminRoute && userStore.isLibrarian"
                variant="primary"
                block
                :prepend-icon="BookOpenIcon"
                @click="goToCirculation"
              >
                前往服务台办理借出
              </Button>
              <Button
                v-else-if="book.available_copies > 0"
                variant="primary"
                block
                :loading="borrowing"
                :prepend-icon="BookOpenIcon"
                @click="handleSelfBorrow"
              >
                立即借阅
              </Button>
              <Button
                v-else
                variant="primary"
                block
                :loading="reserving"
                :prepend-icon="CalendarDaysIcon"
                @click="handleReserve"
              >
                预约排队
              </Button>
              <Button
                v-if="isAdminRoute && userStore.isLibrarian"
                variant="outline"
                block
                :prepend-icon="PlusIcon"
                @click="openAddCopyDialog"
              >
                补录单册
              </Button>
              <a
                v-if="book.source_url"
                :href="book.source_url"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-sm bg-white border border-gray-300 text-gray-700 shadow-sm transition-colors duration-200 hover:bg-gray-50 hover:-translate-y-0.5 hover:shadow focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98] active:translate-y-0"
              >
                <component :is="LinkIcon" class="w-4 h-4" />
                查看数据来源
              </a>
            </div>
          </div>
        </Card>

        <Card>
          <h2 class="text-base font-medium text-gray-900 mb-4">资源属性</h2>
          <dl class="space-y-3 text-sm">
            <div v-for="meta in metaList" :key="meta.label" class="flex items-start justify-between gap-3">
              <dt class="text-gray-500 flex-shrink-0">{{ meta.label }}</dt>
              <dd class="text-gray-900 text-right break-all" :class="meta.mono ? 'font-mono text-xs' : ''">{{ meta.value }}</dd>
            </div>
          </dl>
        </Card>
      </div>

      <!-- 右栏：详情、目录、书评、推荐 -->
      <div class="min-w-0 space-y-4">
        <Card>
          <h1 class="text-2xl font-semibold tracking-tight text-gray-900">{{ book.title }}</h1>
          <p class="text-sm text-gray-600 mt-1">{{ book.author }}</p>

          <div class="flex flex-wrap items-center gap-4 mt-4">
            <RatingStars :model-value="Number(book.rating || 0)" :count="book.rating_count || 0" show-value />
            <div class="flex flex-wrap items-center gap-2">
              <Badge v-if="book.category" variant="primary">{{ book.category.name }}</Badge>
              <Badge v-if="book.format" variant="secondary">{{ book.format }}</Badge>
              <Badge v-if="book.language" variant="secondary">{{ book.language }}</Badge>
              <Badge v-if="book.pages" variant="default">{{ book.pages }} 页</Badge>
            </div>
          </div>

          <div v-if="book.tags" class="flex flex-wrap gap-2 mt-4">
            <span v-for="tag in tagList" :key="tag" class="px-2.5 py-1 rounded-lg bg-gray-100 text-gray-600 text-xs font-medium">{{ tag }}</span>
          </div>
        </Card>

        <Card v-if="book.description">
          <h2 class="text-base font-medium text-gray-900 mb-3">内容简介</h2>
          <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{{ book.description }}</p>
        </Card>

        <Card v-if="book.toc">
          <h2 class="text-base font-medium text-gray-900 mb-3">目录</h2>
          <div class="max-h-80 overflow-y-auto scrollbar-thin rounded-lg bg-gray-50 border border-gray-200 p-4">
            <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line font-mono">{{ book.toc }}</p>
          </div>
        </Card>

        <Card v-if="book.author_bio">
          <h2 class="text-base font-medium text-gray-900 mb-3">作者简介</h2>
          <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{{ book.author_bio }}</p>
        </Card>

        <!-- 单册清册 -->
        <Card padding="none">
          <div class="p-6 pb-4">
            <h2 class="text-base font-medium text-gray-900">馆藏单册（{{ book.copies?.length || 0 }}）</h2>
          </div>
          <div class="overflow-x-auto scrollbar-thin">
            <table class="w-full">
              <thead class="bg-gray-50 border-y border-gray-200">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">条形码</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">状态</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">位置</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                <tr v-for="copy in book.copies" :key="copy.id" class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-3 text-xs font-mono text-gray-700">{{ copy.barcode }}</td>
                  <td class="px-4 py-3">
                    <Badge :variant="copyStatusVariant[copy.status] || 'default'" size="small">
                      {{ copyStatusLabel[copy.status] || copy.status }}
                    </Badge>
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ copy.location_note || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState
            v-if="!book.copies?.length"
            title="暂无单册记录"
            :description="isAdminRoute ? '可点击左侧「补录单册」为该书目新增实体复本' : '该书目暂无可借实体册'"
          />
        </Card>

        <!-- 书评 -->
        <Card>
          <h2 class="text-base font-medium text-gray-900 mb-4">读者书评（{{ reviews.length }}）</h2>

          <div class="rounded-lg bg-gray-50 border border-gray-200 p-4 mb-6">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <span class="text-sm font-medium text-gray-700">{{ myReview ? '更新我的评分书评' : '写下我的评分书评' }}</span>
              <RatingStars v-model="reviewForm.rating" editable />
            </div>
            <Textarea v-model="reviewForm.content" class="mt-3" :rows="3" placeholder="这本书值得推荐吗？说说你的阅读感受（可选）" />
            <div class="flex justify-end gap-3 mt-3">
              <Button
                v-if="myReview"
                variant="outline"
                :prepend-icon="TrashIcon"
                @click="handleDeleteMyReview"
              >
                删除
              </Button>
              <Button variant="primary" :loading="submittingReview" @click="submitReview">
                {{ myReview ? '更新书评' : '发表书评' }}
              </Button>
            </div>
          </div>

          <div v-if="reviews.length" class="space-y-4">
            <div v-for="review in reviews" :key="review.id" class="rounded-lg border border-gray-200 p-4 hover:border-blue-300 transition-colors duration-200">
              <div class="flex items-start justify-between gap-3">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center text-blue-700 font-semibold flex-shrink-0">
                    {{ (review.user?.full_name || review.user?.username || '?').charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900">
                      {{ review.user?.full_name || review.user?.username || '匿名读者' }}
                      <span v-if="review.user_id === userStore.user?.id" class="ml-1 text-xs text-blue-600">我</span>
                    </div>
                    <div class="text-xs text-gray-500">{{ formatDateTime(review.updated_at || review.created_at) }}</div>
                  </div>
                </div>
                <RatingStars :model-value="review.rating" size="small" />
              </div>
              <p v-if="review.content" class="text-sm text-gray-600 mt-3 whitespace-pre-line">{{ review.content }}</p>
            </div>
          </div>
          <EmptyState v-else title="还没有书评" description="成为第一个分享阅读感受的读者" :icon="ChatBubbleLeftRightIcon" />
        </Card>

        <!-- 相似推荐 -->
        <Card v-if="similar.length">
          <h2 class="text-base font-medium text-gray-900 mb-4">同类高分推荐</h2>
          <div class="grid grid-cols-3 sm:grid-cols-4 xl:grid-cols-6 lg:grid-cols-5 gap-4">
            <button
              v-for="item in similar"
              :key="item.book.id"
              type="button"
              class="group text-left focus:outline-none"
              @click="router.push(`${booksPath}/${item.book.id}`)"
            >
              <div class="transition-transform duration-200 group-hover:-translate-y-1">
                <BookCover :book="item.book" ratio="3/4" />
              </div>
              <div class="mt-2 text-sm font-medium text-gray-900 truncate group-hover:text-[#2f5b4e]">{{ item.book.title }}</div>
              <div class="text-xs text-gray-500 truncate mt-0.5">{{ item.book.author }}</div>
            </button>
          </div>
        </Card>
      </div>
    </div>

    <!-- 补录单册：为馆员提供新增实体复本的入口（对应 POST /api/books/{id}/copies） -->
    <Dialog v-model="showAddCopyDialog" title="补录单册" max-width="sm">
      <div class="space-y-4">
        <p class="text-sm text-gray-600">
          为《{{ book?.title || '' }}》新增实体复本，条码需在馆内唯一。
        </p>
        <Input
          v-model="copyForm.count"
          type="number"
          label="新增册数"
          hint="系统按“起始条码 + 序号”自动生成，也可手工修改"
        />
        <Input
          v-model="copyForm.barcode"
          label="起始条码"
          :prepend-icon="QrCodeIcon"
          placeholder="例如 BK-202610-0554-04"
        />
        <Input
          v-model="copyForm.locationNote"
          label="存放位置备注"
          placeholder="选填，例如 C-2F-02-A"
        />
      </div>
      <template #footer>
        <Button variant="outline" @click="showAddCopyDialog = false">取消</Button>
        <Button variant="primary" :loading="addingCopy" @click="handleAddCopy">确认新增</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeftIcon,
  BookOpenIcon,
  CalendarDaysIcon,
  ChatBubbleLeftRightIcon,
  LinkIcon,
  PlusIcon,
  QrCodeIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'
import { useUserStore } from '@/stores/user'
import { booksApi, borrowsApi, reservationsApi, reviewsApi } from '@/api'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Input from '@/components/ui/Input.vue'
import Dialog from '@/components/ui/Dialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import RatingStars from '@/components/ui/RatingStars.vue'
import BookCover from '@/components/ui/BookCover.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isAdminRoute = computed(() => route.path.startsWith('/admin'))
const booksPath = computed(() => (isAdminRoute.value ? '/admin/books' : '/books'))

const book = ref(null)
const reviews = ref([])
const similar = ref([])
const loading = ref(true)
const submittingReview = ref(false)
const reserving = ref(false)
const borrowing = ref(false)

// 详情加载失败时区分「图书不存在(404)」与「服务异常」，避免把 500 显示成已下架
const loadError = ref({ status: 0, message: '' })

const showAddCopyDialog = ref(false)
const addingCopy = ref(false)
const copyForm = reactive({ count: 1, barcode: '', locationNote: '' })

const reviewForm = reactive({ rating: 5, content: '' })

const copyStatusLabel = {
  available: '在架',
  borrowed: '借出',
  reserved: '预约保留',
  maintenance: '维护中',
  lost: '遗失'
}

const copyStatusVariant = {
  available: 'success',
  borrowed: 'warning',
  reserved: 'primary',
  maintenance: 'default',
  lost: 'danger'
}

const metaList = computed(() => {
  const b = book.value || {}
  return [
    { label: 'ISBN', value: b.isbn || '—', mono: true },
    { label: '出版社', value: b.publisher || '—' },
    { label: '出版日期', value: b.publish_date || '—' },
    { label: '语种', value: b.language || '—' },
    { label: '资源格式', value: b.format || '—' },
    { label: '页数', value: b.pages ? `${b.pages} 页` : '—' },
    { label: '文件大小', value: b.file_size || '—', mono: true },
    { label: '所属分类', value: b.category?.name || '—' },
    { label: '书架位置', value: b.location?.name || b.location?.code || '—' },
    { label: '浏览量', value: b.source_views ?? '—' },
    { label: '点赞数', value: b.source_likes ?? '—' },
    { label: '评论数', value: b.source_comments ?? '—' }
  ]
})

const tagList = computed(() => (book.value?.tags || '').split(/[,，\s]+/).filter(Boolean))

const myReview = computed(() => reviews.value.find(r => r.user_id === userStore.user?.id))

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN')
}

async function loadBook() {
  loading.value = true
  loadError.value = { status: 0, message: '' }
  try {
    const { data } = await booksApi.getById(route.params.id)
    book.value = data
  } catch (err) {
    book.value = null
    const status = err.response?.status || 0
    loadError.value = {
      status,
      message:
        status === 404
          ? '图书可能已下架，返回馆藏检索重新检索'
          : err.response?.data?.detail || '服务暂时不可用，请稍后重试'
    }
    window.$toast?.error(status === 404 ? '未找到该图书' : `加载图书详情失败（HTTP ${status || '网络异常'}）`)
  } finally {
    loading.value = false
  }
}

/** 按现有复本序号推算下一个可用条码，格式与导入脚本保持一致 */
function suggestNextBarcode() {
  const copies = book.value?.copies || []
  const month = new Date().toISOString().slice(0, 7).replace('-', '')
  const bookId = String(book.value?.id || '').padStart(4, '0')
  const used = new Set(copies.map(c => c.barcode))
  let candidate = `BK-${month}-${bookId}-${String(copies.length + 1).padStart(2, '0')}`
  let seq = copies.length + 1
  while (used.has(candidate)) {
    seq += 1
    candidate = `BK-${month}-${bookId}-${String(seq).padStart(2, '0')}`
  }
  return candidate
}

/**
 * 依据起始条码推出本次要新增的若干条码。
 * 起始条码形如 BK-202610-0009-04 时依次递增尾号（04/05/…），
 * 否则退化为追加序号（base-01/base-02/…），避免与既有复本条码撞号。
 */
function buildBarcodes(base, count) {
  const matched = base.match(/^(.*?)(\d+)$/)
  if (!matched) {
    return Array.from({ length: count }, (_, i) =>
      count === 1 ? base : `${base}-${String(i + 1).padStart(2, '0')}`
    )
  }
  const [, prefix, digits] = matched
  const start = parseInt(digits, 10)
  return Array.from({ length: count }, (_, i) =>
    `${prefix}${String(start + i).padStart(digits.length, '0')}`
  )
}

function openAddCopyDialog() {
  copyForm.count = 1
  copyForm.barcode = suggestNextBarcode()
  copyForm.locationNote = ''
  showAddCopyDialog.value = true
}

async function handleAddCopy() {
  const count = Math.max(1, Math.min(20, Number(copyForm.count) || 1))
  const base = copyForm.barcode.trim()
  if (!base) {
    window.$toast?.warning('请填写起始条码')
    return
  }
  const barcodes = buildBarcodes(base, count)

  addingCopy.value = true
  try {
    for (const barcode of barcodes) {
      await booksApi.addCopy(route.params.id, { barcode, location_note: copyForm.locationNote.trim() || null })
    }
    window.$toast?.success(`已新增 ${count} 册复本`)
    showAddCopyDialog.value = false
    await loadBook()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '补录单册失败')
  } finally {
    addingCopy.value = false
  }
}

async function loadReviews() {
  try {
    const { data } = await reviewsApi.getByBook(route.params.id)
    reviews.value = data
    const mine = data.find(r => r.user_id === userStore.user?.id)
    if (mine) {
      reviewForm.rating = mine.rating
      reviewForm.content = mine.content || ''
    }
  } catch (err) {
    console.error('加载书评失败', err)
  }
}

async function loadSimilar() {
  try {
    const { data } = await booksApi.getSimilar(route.params.id, 6)
    similar.value = data
  } catch (err) {
    console.error('加载相似推荐失败', err)
  }
}

async function submitReview() {
  submittingReview.value = true
  try {
    await reviewsApi.upsert(route.params.id, { rating: reviewForm.rating, content: reviewForm.content })
    window.$toast?.success('书评已保存')
    await Promise.all([loadReviews(), loadBook()])
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '保存书评失败')
  } finally {
    submittingReview.value = false
  }
}

async function handleDeleteMyReview() {
  if (!myReview.value) return
  try {
    await reviewsApi.remove(myReview.value.id)
    window.$toast?.success('书评已删除')
    reviewForm.rating = 5
    reviewForm.content = ''
    await Promise.all([loadReviews(), loadBook()])
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '删除失败')
  }
}

// 馆员办理：带着当前书目跳转服务台，落地后无需再扫条码
function goToCirculation() {
  router.push({ path: isAdminRoute.value ? '/admin/circulation' : '/circulation', query: { bookId: book.value.id } })
}

async function handleSelfBorrow() {
  borrowing.value = true
  try {
    await borrowsApi.selfBorrow(book.value.id)
    window.$toast?.success('借阅成功，可在「我的书架」查看归还日期')
    await loadBook()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '借阅失败')
  } finally {
    borrowing.value = false
  }
}

async function handleReserve() {
  reserving.value = true
  try {
    await reservationsApi.create(book.value.id)
    window.$toast?.success('预约成功，到书后将通过站内通知提醒')
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '预约失败')
  } finally {
    reserving.value = false
  }
}

onMounted(() => {
  loadBook()
  loadReviews()
  loadSimilar()
})

watch(() => route.params.id, (id) => {
  if (id) {
    loadBook()
    loadReviews()
    loadSimilar()
  }
})
</script>
