<template>
  <div class="neo-page p-6 lg:p-8 max-w-7xl mx-auto">
    <PageHeader title="全馆仪表盘" subtitle="馆藏、流通、读者互动与数字资源的实时总览">
      <template #actions>
        <Button variant="outline" :prepend-icon="ChartBarIcon" @click="router.push('/analytics')">
          查看统计报表
        </Button>
      </template>
    </PageHeader>

    <!-- 全馆核心指标 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <StatCard
        v-for="stat in kpiStats"
        :key="stat.label"
        :label="stat.label"
        :value="stat.value"
        :hint="stat.hint"
        :icon="stat.icon"
        :tone="stat.tone"
      />
    </div>

    <!-- 我的阅读 -->
    <div class="mt-6">
      <Card>
        <div class="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-6">
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-semibold tracking-tight text-gray-900">我的阅读</h2>
            <p class="text-xs text-gray-500 mt-1">与你账号关联的在借、逾期、罚金与通知概览</p>
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
              <div v-for="item in myReading" :key="item.label" class="neo-stat-icon rounded-2xl p-4">
                <div class="text-xs text-gray-500">{{ item.label }}</div>
                <div class="text-2xl font-semibold tracking-tight mt-1" :class="item.tone">
                  {{ item.value }}
                </div>
              </div>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <Button variant="primary" :prepend-icon="BookOpenIcon" @click="router.push('/shelf')">我的书架</Button>
            <Button variant="outline" @click="router.push('/borrows')">借阅中心</Button>
            <Button variant="ghost" @click="router.push('/notifications')">消息通知</Button>
          </div>
        </div>
      </Card>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <!-- 借还趋势 -->
      <Card>
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <h2 class="text-lg font-semibold tracking-tight text-gray-900">借还趋势（近 15 天）</h2>
            <p class="text-xs text-gray-500 mt-1">按日期统计的借出与归还册次</p>
          </div>
          <div class="flex items-center gap-4 flex-shrink-0">
            <span class="flex items-center gap-2 text-xs text-gray-500">
              <span class="inline-block w-4 h-0.5 rounded-full bg-blue-600"></span>借出
            </span>
            <span class="flex items-center gap-2 text-xs text-gray-500">
              <span class="inline-block w-4 h-0.5 rounded-full bg-green-600"></span>归还
            </span>
          </div>
        </div>

        <div v-if="trends.length">
          <svg viewBox="0 0 400 200" class="w-full h-auto mt-4" role="img" aria-label="近 15 天借出与归还趋势折线图">
            <line
              v-for="(y, index) in gridLines"
              :key="`grid-${index}`"
              :x1="0"
              :x2="400"
              :y1="y"
              :y2="y"
              stroke="#e5e7eb"
              stroke-width="1"
            />
            <polygon :points="borrowArea" fill="rgb(219 234 254)" />
            <polyline
              :points="borrowPoints"
              fill="none"
              stroke="rgb(37 99 235)"
              stroke-width="2"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            <polyline
              :points="returnPoints"
              fill="none"
              stroke="rgb(16 185 129)"
              stroke-width="2"
              stroke-dasharray="4"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            <text
              v-for="label in axisLabels"
              :key="`axis-${label.text}-${label.x}`"
              :x="label.x"
              :y="194"
              :text-anchor="label.anchor"
              font-size="10"
              fill="#9ca3af"
            >
              {{ label.text }}
            </text>
          </svg>
          <p class="text-xs text-gray-500 mt-3">
            峰值 {{ peakDay.date }}（借出 {{ peakDay.borrows }} 册）· 区间合计借出
            <span class="text-blue-600 font-medium">{{ totalBorrows }}</span> 册 / 归还
            <span class="text-green-600 font-medium">{{ totalReturns }}</span> 册
          </p>
        </div>
        <EmptyState v-else title="暂无流通数据" description="近 15 天还没有借还记录" :icon="ChartBarIcon" />
      </Card>

      <!-- 热门图书 -->
      <Card>
        <h2 class="text-lg font-semibold tracking-tight text-gray-900">热门图书 Top6</h2>
        <p class="text-xs text-gray-500 mt-1">按累计借阅次数排序</p>

        <div v-if="popularBooks.length" class="mt-4 space-y-2">
          <button
            v-for="(book, index) in popularBooks"
            :key="book.id"
            type="button"
            class="w-full flex items-center gap-3 p-2 rounded-lg text-left transition-all duration-200 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
            @click="router.push(`/books/${book.id}`)"
          >
            <span
              class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold flex-shrink-0"
              :class="index < 3 ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'"
            >
              {{ index + 1 }}
            </span>
            <span class="w-12 flex-shrink-0">
              <BookCover :book="book" ratio="3/4" />
            </span>
            <span class="flex-1 min-w-0">
              <span class="block text-sm font-medium text-gray-900 truncate">{{ book.title }}</span>
              <span class="block text-xs text-gray-500 truncate">{{ book.author }}</span>
            </span>
            <Badge variant="primary" size="small" class="flex-shrink-0">借阅 {{ book.borrow_count }} 次</Badge>
          </button>
        </div>
        <EmptyState v-else title="暂无借阅排行" description="还没有产生借阅记录" :icon="BookOpenIcon" />
      </Card>
    </div>

    <!-- 个性化推荐 -->
    <div class="mt-6">
      <h2 class="text-lg font-semibold tracking-tight text-gray-900">为你推荐</h2>
      <p class="text-xs text-gray-500 mt-1">依据你的借阅历史与馆藏热度生成</p>

      <div v-if="recommendations.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-4">
        <button
          v-for="item in recommendations"
          :key="item.book.id"
          type="button"
          class="neo-card neo-card-hover text-left overflow-hidden transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 active:scale-[0.98]"
          @click="router.push(`/books/${item.book.id}`)"
        >
          <BookCover :book="item.book" ratio="3/4" />
          <span class="block p-6">
            <span class="block text-sm font-semibold tracking-tight text-gray-900 truncate">{{ item.book.title }}</span>
            <span class="block text-xs text-gray-500 mt-1 truncate">{{ item.book.author }}</span>
            <span class="block text-xs text-blue-600 mt-2 line-clamp-2">{{ item.reason }}</span>
          </span>
        </button>
      </div>
      <EmptyState
        v-else
        title="暂无推荐"
        description="多借阅几本书，推荐会更贴合你的口味"
        :icon="SparklesIcon"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <!-- 高分榜 -->
      <Card>
        <h2 class="text-lg font-semibold tracking-tight text-gray-900">读者高分榜 Top6</h2>
        <p class="text-xs text-gray-500 mt-1">按平均评分与评分人数排序</p>

        <div v-if="topRatedBooks.length" class="mt-4 space-y-2">
          <!-- 评分星标本身是可交互组件，故与跳转按钮并排而非嵌套 -->
          <div
            v-for="(book, index) in topRatedBooks"
            :key="book.id"
            class="flex items-center gap-3 p-2 rounded-lg transition-all duration-200 hover:bg-gray-50"
          >
            <span
              class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold flex-shrink-0"
              :class="index < 3 ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'"
            >
              {{ index + 1 }}
            </span>
            <button
              type="button"
              class="flex items-center gap-3 flex-1 min-w-0 text-left rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
              @click="router.push(`/books/${book.id}`)"
            >
              <span class="w-12 flex-shrink-0">
                <BookCover :book="book" ratio="3/4" />
              </span>
              <span class="flex-1 min-w-0">
                <span class="block text-sm font-medium text-gray-900 truncate">{{ book.title }}</span>
                <span class="block text-xs text-gray-500 truncate">{{ book.author }}</span>
              </span>
            </button>
            <RatingStars
              class="flex-shrink-0"
              :model-value="Number(book.rating || 0)"
              :count="book.rating_count || 0"
              size="small"
              show-value
            />
          </div>
        </div>
        <EmptyState v-else title="暂无评分数据" description="还没有读者留下评分" :icon="StarIcon" />
      </Card>

      <!-- 馆内公告 -->
      <Card>
        <h2 class="text-lg font-semibold tracking-tight text-gray-900">馆内公告</h2>
        <p class="text-xs text-gray-500 mt-1">最新发布的生效公告</p>

        <div v-if="announcements.length" class="mt-4 space-y-3 max-h-96 overflow-y-auto">
          <div
            v-for="ann in announcements"
            :key="ann.id"
            class="p-4 rounded-lg border border-gray-200 transition-all duration-200 hover:border-blue-300"
          >
            <div class="flex items-start justify-between gap-3">
              <Badge :variant="priorityOf(ann.priority).variant" size="small">
                {{ priorityOf(ann.priority).label }}
              </Badge>
              <span class="text-xs text-gray-500 flex-shrink-0">{{ formatDate(ann.created_at) }}</span>
            </div>
            <div class="text-sm font-medium text-gray-900 mt-2">{{ ann.title }}</div>
            <p class="text-xs text-gray-600 mt-1">{{ ann.content }}</p>
          </div>
        </div>
        <EmptyState v-else title="暂无公告" description="当前没有生效中的馆内公告" :icon="MegaphoneIcon" />
      </Card>
    </div>

    <!-- 馆藏结构 -->
    <div class="mt-6">
      <Card>
        <h2 class="text-lg font-semibold tracking-tight text-gray-900">馆藏结构</h2>
        <p class="text-xs text-gray-500 mt-1">按分类、资源格式与语种统计的藏书分布</p>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-6">
          <!-- 分类分布 -->
          <div>
            <h3 class="text-sm font-semibold text-gray-900">分类分布</h3>
            <div v-if="categoryStats.length" class="mt-4 space-y-4">
              <div v-for="cat in categoryStats" :key="cat.id">
                <div class="flex items-center justify-between text-xs mb-1.5">
                  <span class="text-gray-600 truncate">{{ cat.name }}</span>
                  <span class="text-gray-500 ml-2 flex-shrink-0">{{ cat.count }} 本 · {{ cat.percent }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full transition-all duration-200"
                    :style="{ width: `${cat.percent}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <EmptyState v-else title="暂无分类数据" description="尚未维护图书分类" :icon="Squares2X2Icon" />
          </div>

          <!-- 资源格式分布 -->
          <div>
            <h3 class="text-sm font-semibold text-gray-900">资源格式分布</h3>
            <div v-if="formatStats.length" class="mt-4 space-y-4">
              <div v-for="fmt in formatStats" :key="fmt.format">
                <div class="flex items-center justify-between text-xs mb-1.5">
                  <span class="text-gray-600 truncate">{{ fmt.format }}</span>
                  <span class="text-gray-500 ml-2 flex-shrink-0">{{ fmt.count }} 种 · {{ fmt.percent }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full transition-all duration-200"
                    :style="{ width: `${fmt.percent}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <EmptyState v-else title="暂无格式数据" description="尚未登记电子资源格式" :icon="DocumentIcon" />
          </div>

          <!-- 语种分布 -->
          <div>
            <h3 class="text-sm font-semibold text-gray-900">语种分布</h3>
            <div v-if="languageStats.length" class="mt-4 space-y-4">
              <div v-for="lang in languageStats" :key="lang.language">
                <div class="flex items-center justify-between text-xs mb-1.5">
                  <span class="text-gray-600 truncate">{{ languageLabel(lang.language) }}</span>
                  <span class="text-gray-500 ml-2 flex-shrink-0">{{ lang.count }} 种 · {{ lang.percent }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full transition-all duration-200"
                    :style="{ width: `${lang.percent}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <EmptyState v-else title="暂无语种数据" description="尚未登记图书语种" :icon="LanguageIcon" />
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowPathIcon,
  BookOpenIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  DocumentIcon,
  ExclamationTriangleIcon,
  LanguageIcon,
  MegaphoneIcon,
  SparklesIcon,
  Squares2X2Icon,
  StarIcon,
  UsersIcon
} from '@heroicons/vue/24/outline'
import PageHeader from '@/components/ui/PageHeader.vue'
import Card from '@/components/ui/Card.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import BookCover from '@/components/ui/BookCover.vue'
import RatingStars from '@/components/ui/RatingStars.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { statsApi, recommendApi, announcementsApi } from '@/api'

const router = useRouter()

const overview = ref({})
const trends = ref([])
const recommendations = ref([])
const popularBooks = ref([])
const topRatedBooks = ref([])
const categories = ref([])
const formats = ref([])
const languages = ref([])
const announcements = ref([])

// 各区块独立加载，单个接口失败不影响其他区块渲染
const loadOverview = async () => {
  try {
    overview.value = (await statsApi.getOverview()).data || {}
  } catch (err) {
    console.error('仪表盘：全馆概览加载失败', err)
  }
}

const loadTrends = async () => {
  try {
    trends.value = (await statsApi.getTrends(15)).data || []
  } catch (err) {
    console.error('仪表盘：借还趋势加载失败', err)
  }
}

const loadRecommendations = async () => {
  try {
    recommendations.value = (await recommendApi.getList(6)).data || []
  } catch (err) {
    console.error('仪表盘：个性化推荐加载失败', err)
  }
}

const loadPopularBooks = async () => {
  try {
    popularBooks.value = (await statsApi.getPopularBooks(6)).data || []
  } catch (err) {
    console.error('仪表盘：热门图书加载失败', err)
  }
}

const loadTopRatedBooks = async () => {
  try {
    topRatedBooks.value = (await statsApi.getTopRated(6)).data || []
  } catch (err) {
    console.error('仪表盘：高分榜加载失败', err)
  }
}

const loadCategories = async () => {
  try {
    categories.value = (await statsApi.getCategories()).data || []
  } catch (err) {
    console.error('仪表盘：分类分布加载失败', err)
  }
}

const loadFormats = async () => {
  try {
    formats.value = (await statsApi.getFormats()).data || []
  } catch (err) {
    console.error('仪表盘：资源格式分布加载失败', err)
  }
}

const loadLanguages = async () => {
  try {
    languages.value = (await statsApi.getLanguages()).data || []
  } catch (err) {
    console.error('仪表盘：语种分布加载失败', err)
  }
}

const loadAnnouncements = async () => {
  try {
    announcements.value = (await announcementsApi.getActive()).data || []
  } catch (err) {
    console.error('仪表盘：馆内公告加载失败', err)
  }
}

const kpiStats = computed(() => {
  const data = overview.value
  return [
    {
      label: '馆藏图书',
      value: data.total_books ?? 0,
      hint: `${data.total_copies ?? 0} 册（含复本）`,
      icon: BookOpenIcon,
      tone: 'primary'
    },
    {
      label: '在借流通',
      value: data.active_borrows ?? 0,
      hint: '尚未归还的借阅记录',
      icon: ArrowPathIcon,
      tone: 'success'
    },
    {
      label: '逾期预警',
      value: data.overdue_borrows ?? 0,
      hint: '已超过应还日期',
      icon: ExclamationTriangleIcon,
      tone: 'danger'
    },
    {
      label: '注册读者',
      value: data.total_readers ?? 0,
      hint: '读者账号总数',
      icon: UsersIcon,
      tone: 'primary'
    },
    {
      label: '书评总数',
      value: data.total_reviews ?? 0,
      hint: '读者公开书评数量',
      icon: ChatBubbleLeftRightIcon,
      tone: 'neutral'
    },
    {
      label: '平均评分',
      value: Number(data.avg_rating ?? 0).toFixed(1),
      hint: '有评分图书的平均星级',
      icon: StarIcon,
      tone: 'warning'
    }
  ]
})

const myReading = computed(() => {
  const data = overview.value
  const fines = Number(data.user_fines ?? 0)
  const overdue = data.user_overdue ?? 0
  const unread = data.unread_notifications ?? 0
  return [
    { label: '在借图书', value: data.user_borrowed ?? 0, tone: 'text-gray-900' },
    { label: '逾期未还', value: overdue, tone: overdue > 0 ? 'text-red-600' : 'text-gray-900' },
    { label: '未缴罚金', value: `¥${fines.toFixed(2)}`, tone: fines > 0 ? 'text-amber-600' : 'text-gray-900' },
    { label: '未读通知', value: unread, tone: unread > 0 ? 'text-blue-600' : 'text-gray-900' }
  ]
})

// 折线图绘图区（viewBox 400×200）
const CHART = { left: 10, top: 16, width: 380, height: 156 }

const trendMax = computed(() => {
  const values = trends.value.flatMap((item) => [Number(item.borrows) || 0, Number(item.returns) || 0])
  return Math.max(1, ...values)
})

const pointFor = (index, value) => {
  const count = trends.value.length
  const x = CHART.left + (count > 1 ? (index / (count - 1)) * CHART.width : CHART.width / 2)
  const y = CHART.top + CHART.height - ((Number(value) || 0) / trendMax.value) * CHART.height
  return `${x.toFixed(1)},${y.toFixed(1)}`
}

const borrowPoints = computed(() => trends.value.map((item, index) => pointFor(index, item.borrows)).join(' '))

const returnPoints = computed(() => trends.value.map((item, index) => pointFor(index, item.returns)).join(' '))

const borrowArea = computed(() => {
  if (!borrowPoints.value) return ''
  const baseline = CHART.top + CHART.height
  return `${CHART.left},${baseline} ${borrowPoints.value} ${CHART.left + CHART.width},${baseline}`
})

const gridLines = computed(() =>
  Array.from({ length: 5 }, (_, index) => CHART.top + (index / 4) * CHART.height)
)

const axisLabels = computed(() => {
  const count = trends.value.length
  if (!count) return []
  const indexes = count > 2 ? [...new Set([0, Math.floor((count - 1) / 2), count - 1])] : trends.value.map((_, i) => i)
  return indexes.map((index) => ({
    x: CHART.left + (count > 1 ? (index / (count - 1)) * CHART.width : CHART.width / 2),
    text: trends.value[index].date,
    anchor: index === 0 ? 'start' : index === count - 1 ? 'end' : 'middle'
  }))
})

const peakDay = computed(() => {
  if (!trends.value.length) return { date: '-', borrows: 0 }
  return trends.value.reduce(
    (best, item) => {
      const borrows = Number(item.borrows) || 0
      return borrows > best.borrows ? { date: item.date, borrows } : best
    },
    { date: trends.value[0].date, borrows: Number(trends.value[0].borrows) || 0 }
  )
})

const totalBorrows = computed(() => trends.value.reduce((sum, item) => sum + (Number(item.borrows) || 0), 0))

const totalReturns = computed(() => trends.value.reduce((sum, item) => sum + (Number(item.returns) || 0), 0))

const withPercent = (rows, key) => {
  const total = rows.reduce((sum, row) => sum + (Number(row[key]) || 0), 0)
  return rows.map((row) => ({
    ...row,
    percent: total > 0 ? Math.round(((Number(row[key]) || 0) / total) * 100) : 0
  }))
}

const categoryStats = computed(() => withPercent(categories.value, 'count'))
const formatStats = computed(() => withPercent(formats.value, 'count'))
const languageStats = computed(() => withPercent(languages.value, 'count'))

const languageNames = {
  zh: '中文',
  en: '英文',
  ja: '日文',
  ko: '韩文',
  fr: '法文',
  de: '德文',
  ru: '俄文',
  es: '西班牙文'
}

const languageLabel = (code) => languageNames[code] || code

const priorityMeta = {
  urgent: { label: '紧急', variant: 'danger' },
  important: { label: '重要', variant: 'warning' },
  normal: { label: '一般', variant: 'default' }
}

const priorityOf = (priority) => priorityMeta[priority] || priorityMeta.normal

const formatDate = (value) => (value ? new Date(value).toLocaleDateString('zh-CN') : '-')

onMounted(() => {
  Promise.all([
    loadOverview(),
    loadTrends(),
    loadRecommendations(),
    loadPopularBooks(),
    loadTopRatedBooks(),
    loadCategories(),
    loadFormats(),
    loadLanguages(),
    loadAnnouncements()
  ])
})
</script>
