<template>
  <div class="neo-page">
    <!-- 全馆核心指标 -->
    <div class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <StatCard
        v-for="stat in kpiStats"
        :key="stat.label"
        :label="stat.label"
        :value="stat.value"
        :icon="stat.icon"
        :tone="stat.tone"
      />
    </div>

    <div class="mt-4">
      <Card>
        <h2 class="text-base font-medium text-gray-900">热门图书 Top6</h2>
        <p class="text-xs text-gray-500 mt-1">按累计借阅次数排序</p>

        <div v-if="popularBooks.length" class="mt-4 space-y-2">
          <button
            v-for="(book, index) in popularBooks"
            :key="book.id"
            type="button"
            class="w-full flex items-center gap-3 p-2 rounded-lg text-left transition-colors duration-200 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
            @click="router.push(`/books/${book.id}`)"
          >
            <span
              class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold flex-shrink-0"
              :class="index < 3 ? 'text-[#2f5b4e] bg-[#e8f0eb]' : 'text-gray-500 bg-[#f2f3f5]'"
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
    <Card class="mt-4">
      <div class="flex items-end justify-between gap-4">
        <div>
          <h2 class="flex items-center gap-2 text-base font-medium text-gray-900">
            <SparklesIcon class="w-5 h-5 text-[#2f5b4e]" />为你推荐
          </h2>
          <p class="text-xs text-gray-500 mt-1">依据你的借阅历史与馆藏热度生成</p>
        </div>
        <RouterLink to="/books" class="text-sm text-[#2f5b4e] hover:text-[#487a69]">查看更多</RouterLink>
      </div>

      <div v-if="recommendations.length" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-5 mt-5">
        <button
          v-for="item in recommendations"
          :key="item.book.id"
          type="button"
          class="group text-left focus:outline-none"
          @click="router.push(`/books/${item.book.id}`)"
        >
          <div class="transition-transform duration-200 group-hover:-translate-y-1">
            <BookCover :book="item.book" ratio="3/4" />
          </div>
          <span class="block mt-3 text-sm font-medium text-gray-900 truncate group-hover:text-[#2f5b4e]">{{ item.book.title }}</span>
          <span class="block text-xs text-gray-500 mt-0.5 truncate">{{ item.book.author }}</span>
          <span class="mt-2 inline-block max-w-full truncate rounded bg-[#e8f0eb] px-1.5 py-0.5 text-[11px] text-[#2f5b4e]">{{ item.reason }}</span>
        </button>
      </div>
      <EmptyState
        v-else
        title="暂无推荐"
        description="多借阅几本书，推荐会更贴合你的口味"
        :icon="SparklesIcon"
      />
    </Card>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
      <!-- 高分榜 -->
      <Card>
        <h2 class="text-base font-medium text-gray-900">读者高分榜 Top6</h2>
        <p class="text-xs text-gray-500 mt-1">按平均评分与评分人数排序</p>

        <div v-if="topRatedBooks.length" class="mt-4 space-y-2">
          <!-- 评分星标本身是可交互组件，故与跳转按钮并排而非嵌套 -->
          <div
            v-for="(book, index) in topRatedBooks"
            :key="book.id"
            class="flex items-center gap-3 p-2 rounded-lg transition-colors duration-200 hover:bg-gray-50"
          >
            <span
              class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold flex-shrink-0"
              :class="index < 3 ? 'text-[#2f5b4e] bg-[#e8f0eb]' : 'text-gray-500 bg-[#f2f3f5]'"
            >
              {{ index + 1 }}
            </span>
            <button
              type="button"
              class="flex items-center gap-3 flex-1 min-w-0 text-left rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
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
        <h2 class="text-base font-medium text-gray-900">馆内公告</h2>
        <p class="text-xs text-gray-500 mt-1">最新发布的生效公告</p>

        <div v-if="announcements.length" class="mt-4 space-y-3 max-h-96 overflow-y-auto">
          <div
            v-for="ann in announcements"
            :key="ann.id"
            class="p-4 rounded-lg border border-gray-200 transition-colors duration-200 hover:border-blue-300"
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
    <div class="mt-4">
      <Card>
        <h2 class="text-base font-medium text-gray-900">馆藏结构</h2>
        <p class="text-xs text-gray-500 mt-1">按分类、资源格式与语种统计的藏书分布</p>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-4">
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
                    class="bg-blue-600 h-2 rounded-full transition-colors duration-200"
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
                    class="bg-blue-600 h-2 rounded-full transition-colors duration-200"
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
                    class="bg-blue-600 h-2 rounded-full transition-colors duration-200"
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
import Card from '@/components/ui/Card.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Badge from '@/components/ui/Badge.vue'
import BookCover from '@/components/ui/BookCover.vue'
import RatingStars from '@/components/ui/RatingStars.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { statsApi, recommendApi, announcementsApi } from '@/api'
import { languageLabel } from '@/utils/labels'

const router = useRouter()
const overview = ref({})
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

// 语种展示统一走 @/utils/labels，避免各页面各写一套映射

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
