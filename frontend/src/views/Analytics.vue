<template>
  <div class="neo-page">
    <PageHeader title="统计报表" subtitle="借还趋势、馆藏结构与读者活跃度">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadAll">
          刷新数据
        </Button>
      </template>
    </PageHeader>

    <!-- 概览指标 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 lg:gap-4 mb-6">
      <StatCard
        label="馆藏图书"
        :value="overview.total_books || 0"
        :hint="`共 ${overview.total_copies || 0} 册馆藏`"
        :icon="BookOpenIcon"
        tone="primary"
      />
      <StatCard
        label="在借流通"
        :value="overview.active_borrows || 0"
        :hint="`今日借出 ${overview.today_borrows || 0} 册`"
        :icon="ArrowPathIcon"
        tone="success"
      />
      <StatCard
        label="逾期预警"
        :value="overview.overdue_borrows || 0"
        hint="需要催还处理"
        :icon="ExclamationTriangleIcon"
        tone="danger"
      />
      <StatCard
        label="书评总数"
        :value="overview.total_reviews || 0"
        hint="读者已发布的书评"
        :icon="ChatBubbleLeftRightIcon"
        tone="neutral"
      />
      <StatCard
        label="平均评分"
        :value="avgRating"
        hint="全馆书目平均星级"
        :icon="StarIcon"
        tone="warning"
      />
    </div>

    <Card padding="normal">
      <Tabs :tabs="tabNames" v-model="activeTab">
        <!-- 1. 流通趋势 -->
        <template #panel-0>
          <div v-if="loading" class="py-12 text-center text-sm text-gray-500">趋势数据加载中…</div>
          <div v-else-if="!trends.length">
            <EmptyState title="暂无流通记录" description="近 30 天没有借出或归还数据" />
          </div>
          <div v-else>
            <div class="flex items-start justify-between gap-4 mb-4">
              <div>
                <h3 class="text-base font-medium text-gray-900">近 {{ trends.length }} 天借还走势</h3>
                <p class="text-sm text-gray-600 mt-1">
                  峰值日期 {{ peakDay.date }} · 当日借出 {{ peakDay.borrows }} 册、归还 {{ peakDay.returns }} 册
                </p>
              </div>
              <div class="flex items-center gap-4 flex-shrink-0">
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded-full bg-blue-600"></span>
                  <span class="text-sm text-gray-600">借出</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="w-0.5 h-3 bg-green-600"></span>
                  <span class="text-sm text-gray-600">归还</span>
                </div>
              </div>
            </div>

            <div class="flex gap-3">
              <div class="relative w-10 h-60 flex-shrink-0">
                <span
                  v-for="tick in chart.yTicks"
                  :key="tick.value"
                  class="absolute right-0 -translate-y-1/2 text-xs text-gray-400"
                  :style="{ top: tick.top }"
                >
                  {{ tick.value }}
                </span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="h-60 w-full">
                  <svg
                    viewBox="0 0 600 240"
                    preserveAspectRatio="none"
                    class="w-full h-full"
                    role="img"
                    aria-label="近 30 天借出与归还数量折线图"
                  >
                    <line
                      v-for="line in chart.gridLines"
                      :key="line.y"
                      x1="0"
                      x2="600"
                      :y1="line.y"
                      :y2="line.y"
                      stroke="#e5e6eb"
                      stroke-width="1"
                      vector-effect="non-scaling-stroke"
                    />
                    <polyline
                      :points="chart.borrowPoints"
                      fill="none"
                      stroke="#2f5b4e"
                      stroke-width="2"
                      vector-effect="non-scaling-stroke"
                    />
                    <polyline
                      :points="chart.returnPoints"
                      fill="none"
                      stroke="#6a9584"
                      stroke-width="2"
                      stroke-dasharray="4"
                      vector-effect="non-scaling-stroke"
                    />
                  </svg>
                </div>
                <div class="flex justify-between mt-2 text-xs text-gray-500">
                  <span v-for="(label, index) in chart.xLabels" :key="index">{{ label }}</span>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4 pt-6 border-t border-gray-200">
              <div>
                <div class="text-sm text-gray-500">总借出</div>
                <div class="text-2xl font-semibold tracking-tight text-blue-600 mt-1">{{ trendSummary.borrows }}</div>
              </div>
              <div>
                <div class="text-sm text-gray-500">总归还</div>
                <div class="text-2xl font-semibold tracking-tight text-green-600 mt-1">{{ trendSummary.returns }}</div>
              </div>
              <div>
                <div class="text-sm text-gray-500">日均借出</div>
                <div class="text-2xl font-semibold tracking-tight text-gray-900 mt-1">{{ trendSummary.dailyAvg }}</div>
              </div>
            </div>
          </div>
        </template>

        <!-- 2. 馆藏结构 -->
        <template #panel-1>
          <div v-if="loading" class="py-12 text-center text-sm text-gray-500">馆藏数据加载中…</div>
          <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <h3 class="text-base font-medium text-gray-900 mb-4">分类藏书榜</h3>
              <EmptyState v-if="!categoryRows.length" title="暂无分类数据" />
              <div v-else class="space-y-4">
                <div v-for="cat in categoryRows" :key="cat.id">
                  <div class="flex items-center justify-between gap-3 text-sm">
                    <span class="text-gray-700 truncate">{{ cat.name }}</span>
                    <span class="text-gray-500 flex-shrink-0">{{ cat.count }} 种 · {{ cat.percent }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2 mt-1.5">
                    <div class="bg-blue-600 h-2 rounded-full" :style="{ width: `${cat.percent}%` }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 class="text-base font-medium text-gray-900 mb-4">语种分布</h3>
              <EmptyState v-if="!languageRows.length" title="暂无语种数据" />
              <div v-else class="space-y-4">
                <div v-for="lang in languageRows" :key="lang.language">
                  <div class="flex items-center justify-between gap-3 text-sm">
                    <span class="text-gray-700 truncate">{{ languageLabel(lang.language) }}</span>
                    <span class="text-gray-500 flex-shrink-0">{{ lang.count }} 种 · {{ lang.percent }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2 mt-1.5">
                    <div class="bg-green-600 h-2 rounded-full" :style="{ width: `${lang.percent}%` }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 3. 读者榜单 -->
        <template #panel-2>
          <div v-if="loading" class="py-12 text-center text-sm text-gray-500">榜单数据加载中…</div>
          <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <h3 class="text-base font-medium text-gray-900 mb-4">借阅热度榜</h3>
              <EmptyState v-if="!popularBooks.length" title="暂无借阅记录" description="还没有图书产生借阅" />
              <div v-else class="-mx-2">
                <RouterLink
                  v-for="(book, index) in popularBooks"
                  :key="book.id"
                  :to="`/admin/books/${book.id}`"
                  class="flex items-center gap-3 px-2 py-2 rounded-lg transition-colors duration-150 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
                >
                  <span class="w-6 text-center text-sm font-semibold text-gray-400 flex-shrink-0">{{ index + 1 }}</span>
                  <div class="w-10 flex-shrink-0 rounded-lg overflow-hidden">
                    <BookCover :book="book" ratio="3/4" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-900 truncate">{{ book.title }}</div>
                    <div class="text-xs text-gray-500 truncate">{{ book.author || '佚名' }}</div>
                  </div>
                  <Badge variant="primary" size="small" class="flex-shrink-0">借阅 {{ book.borrow_count }} 次</Badge>
                </RouterLink>
              </div>
            </div>

            <div>
              <h3 class="text-base font-medium text-gray-900 mb-4">读者高分榜</h3>
              <EmptyState v-if="!topRated.length" title="暂无评分数据" description="还没有读者对图书评分" />
              <div v-else class="-mx-2">
                <RouterLink
                  v-for="(book, index) in topRated"
                  :key="book.id"
                  :to="`/admin/books/${book.id}`"
                  class="flex items-center gap-3 px-2 py-2 rounded-lg transition-colors duration-150 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]"
                >
                  <span class="w-6 text-center text-sm font-semibold text-gray-400 flex-shrink-0">{{ index + 1 }}</span>
                  <div class="w-10 flex-shrink-0 rounded-lg overflow-hidden">
                    <BookCover :book="book" ratio="3/4" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-900 truncate">{{ book.title }}</div>
                    <div class="text-xs text-gray-500 truncate">{{ book.author || '佚名' }}</div>
                  </div>
                  <RatingStars
                    :model-value="book.rating"
                    :count="book.rating_count"
                    size="small"
                    show-value
                    class="flex-shrink-0"
                  />
                </RouterLink>
              </div>
            </div>

            <div class="lg:col-span-2">
              <h3 class="text-base font-medium text-gray-900 mb-4">活跃读者榜</h3>
              <div v-if="!activeReaders.length">
                <EmptyState title="暂无读者借阅数据" />
              </div>
              <div v-else class="overflow-x-auto scrollbar-thin">
                <table class="w-full">
                  <thead class="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">姓名</th>
                      <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">卡号</th>
                      <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">累计借阅</th>
                      <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">在借</th>
                      <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600">逾期</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200">
                    <tr
                      v-for="reader in activeReaders"
                      :key="reader.user_id"
                      class="hover:bg-gray-50 transition-colors"
                    >
                      <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ reader.full_name }}</td>
                      <td class="px-4 py-3 text-sm text-gray-600 font-mono">{{ reader.card_number || '-' }}</td>
                      <td class="px-4 py-3 text-sm text-gray-900">{{ reader.borrow_total }}</td>
                      <td class="px-4 py-3 text-sm text-gray-600">{{ reader.active_borrows }}</td>
                      <td class="px-4 py-3 text-sm">
                        <Badge :variant="reader.overdue > 0 ? 'danger' : 'success'" size="small">
                          {{ reader.overdue }}
                        </Badge>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </template>

        <!-- 4. 资源格式 -->
        <template #panel-3>
          <div v-if="loading" class="py-12 text-center text-sm text-gray-500">资源数据加载中…</div>
          <div v-else>
            <h3 class="text-base font-medium text-gray-900 mb-4">电子资源格式分布</h3>
            <EmptyState v-if="!formatRows.length" title="暂无格式数据" description="书目尚未标注资源格式" />
            <div v-else class="space-y-4">
              <div v-for="item in formatRows" :key="item.format">
                <div class="flex items-center justify-between gap-3 text-sm">
                  <span class="text-gray-700 font-mono">{{ item.format.toUpperCase() }}</span>
                  <span class="text-gray-500 flex-shrink-0">
                    {{ item.count }} 种 · 在架 {{ item.available }} 册 · {{ item.percent }}%
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2 mt-1.5">
                  <div class="bg-blue-600 h-2 rounded-full" :style="{ width: `${item.percent}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </Tabs>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  ArrowPathIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  StarIcon
} from '@heroicons/vue/24/outline'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Tabs from '@/components/ui/Tabs.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import BookCover from '@/components/ui/BookCover.vue'
import RatingStars from '@/components/ui/RatingStars.vue'
import { statsApi } from '@/api'
import { languageLabel } from '@/utils/labels'

const TREND_DAYS = 30

const tabNames = ['流通趋势', '馆藏结构', '读者榜单', '资源格式']

const activeTab = ref(0)
const loading = ref(false)

const overview = ref({})
const trends = ref([])
const categories = ref([])
const languages = ref([])
const popularBooks = ref([])
const topRated = ref([])
const activeReaders = ref([])
const formats = ref([])

const avgRating = computed(() => Number(overview.value.avg_rating || 0).toFixed(1))

const percent = (value, total) => (total > 0 ? Math.round((value / total) * 100) : 0)

const categoryRows = computed(() => {
  const total = categories.value.reduce((sum, c) => sum + (c.count || 0), 0)
  return [...categories.value]
    .sort((a, b) => (b.count || 0) - (a.count || 0))
    .map(c => ({ ...c, percent: percent(c.count || 0, total) }))
})

const languageRows = computed(() => {
  const total = languages.value.reduce((sum, l) => sum + (l.count || 0), 0)
  return languages.value.map(l => ({ ...l, percent: percent(l.count || 0, total) }))
})

const formatRows = computed(() => {
  const total = formats.value.reduce((sum, f) => sum + (f.count || 0), 0)
  return formats.value.map(f => ({ ...f, percent: percent(f.count || 0, total) }))
})

const peakDay = computed(() => {
  if (!trends.value.length) return { date: '-', borrows: 0, returns: 0 }
  return trends.value.reduce((best, day) => (day.borrows > best.borrows ? day : best), trends.value[0])
})

const trendSummary = computed(() => {
  const days = trends.value
  const borrows = days.reduce((sum, d) => sum + d.borrows, 0)
  const returns = days.reduce((sum, d) => sum + d.returns, 0)
  return {
    borrows,
    returns,
    dailyAvg: days.length ? (borrows / days.length).toFixed(1) : '0.0'
  }
})

// 纯 SVG 折线：viewBox 固定 600x240，网格与折线按最大值等比缩放
const chart = computed(() => {
  const days = trends.value
  const count = days.length
  if (!count) return { gridLines: [], yTicks: [], xLabels: [], borrowPoints: '', returnPoints: '' }

  const maxValue = Math.max(1, ...days.map(d => Math.max(d.borrows, d.returns)))
  const top = 10
  const bottom = 230
  const left = 6
  const right = 594
  const stepX = count > 1 ? (right - left) / (count - 1) : 0
  const toY = value => bottom - (value / maxValue) * (bottom - top)

  const gridLines = []
  const yTicks = []
  for (let i = 0; i <= 4; i++) {
    const y = bottom - (i / 4) * (bottom - top)
    gridLines.push({ y })
    yTicks.push({
      value: Math.round((maxValue * i) / 4),
      top: `${(y / 240) * 100}%`
    })
  }

  const pointsOf = key => days.map((d, i) => `${left + i * stepX},${toY(d[key])}`).join(' ')

  const indexes = [...new Set([0, Math.round((count - 1) / 4), Math.round((count - 1) / 2), Math.round(((count - 1) * 3) / 4), count - 1])]

  return {
    gridLines,
    yTicks: yTicks.reverse(),
    xLabels: indexes.map(i => days[i].date),
    borrowPoints: pointsOf('borrows'),
    returnPoints: pointsOf('returns')
  }
})

const loadAll = async () => {
  loading.value = true
  try {
    const [overviewRes, trendsRes, categoriesRes, languagesRes, popularRes, topRes, readersRes, formatsRes] =
      await Promise.all([
        statsApi.getOverview(),
        statsApi.getTrends(TREND_DAYS),
        statsApi.getCategories(),
        statsApi.getLanguages(),
        statsApi.getPopularBooks(10),
        statsApi.getTopRated(10),
        statsApi.getActiveReaders(10),
        statsApi.getFormats()
      ])

    overview.value = overviewRes.data
    trends.value = trendsRes.data
    categories.value = categoriesRes.data
    languages.value = languagesRes.data
    popularBooks.value = popularRes.data
    topRated.value = topRes.data
    activeReaders.value = readersRes.data
    formats.value = formatsRes.data
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '统计数据加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAll()
})
</script>
