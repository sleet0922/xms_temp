<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">全馆仪表盘</h1>
        <p class="text-gray-600 mt-1">实时流通概览与统计分析</p>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card hover v-for="(stat, index) in kpiStats" :key="index">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 mb-1">{{ stat.label }}</div>
              <div class="text-2xl font-bold text-gray-900">{{ stat.value }}</div>
              <div v-if="stat.sublabel" class="text-xs text-gray-500 mt-1">{{ stat.sublabel }}</div>
            </div>
            <div :class="`w-12 h-12 rounded-lg ${stat.bgColor} flex items-center justify-center`">
              <component :is="stat.icon" :class="`w-6 h-6 ${stat.iconColor}`" />
            </div>
          </div>
        </Card>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- Trend Chart -->
        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">借还趋势（近15天）</h3>
          <div class="h-64">
            <svg viewBox="0 0 400 200" class="w-full h-full">
              <defs>
                <linearGradient id="borrowGradient" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stop-color="rgb(37, 99, 235)" stop-opacity="0.2"/>
                  <stop offset="100%" stop-color="rgb(37, 99, 235)" stop-opacity="0"/>
                </linearGradient>
              </defs>

              <!-- Grid lines -->
              <line v-for="i in 5" :key="'grid-'+i" :x1="0" :x2="400" :y1="i * 40" :y2="i * 40" stroke="#e5e7eb" stroke-width="1"/>

              <!-- Borrow line -->
              <polyline :points="borrowPoints" fill="none" stroke="rgb(37, 99, 235)" stroke-width="2"/>
              <polygon :points="borrowAreaPoints" fill="url(#borrowGradient)"/>

              <!-- Return line -->
              <polyline :points="returnPoints" fill="none" stroke="rgb(16, 185, 129)" stroke-width="2" stroke-dasharray="4"/>
            </svg>
            <div class="flex justify-center gap-6 mt-4">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-blue-600"></div>
                <span class="text-sm text-gray-600">借出</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-green-600"></div>
                <span class="text-sm text-gray-600">归还</span>
              </div>
            </div>
          </div>
        </Card>

        <!-- Popular Books -->
        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">热门图书排行</h3>
          <div class="space-y-3">
            <div v-for="(book, index) in popularBooks" :key="book.id" class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
              <div :class="`w-8 h-8 rounded-lg flex items-center justify-center font-bold ${index < 3 ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`">
                {{ index + 1 }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-gray-900 truncate">{{ book.title }}</div>
                <div class="text-xs text-gray-500">{{ book.author }}</div>
              </div>
              <Badge variant="primary">{{ book.borrow_count }}次</Badge>
            </div>
          </div>
        </Card>
      </div>

      <!-- Category Stats & Announcements -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Categories -->
        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">馆藏分类统计</h3>
          <div class="space-y-3">
            <div v-for="cat in categoryStats" :key="cat.id">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-700">{{ cat.name }}</span>
                <span class="text-gray-500">{{ cat.book_count }} 本</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-blue-600 h-2 rounded-full transition-all duration-200" :style="{ width: `${cat.percentage}%` }"></div>
              </div>
            </div>
          </div>
        </Card>

        <!-- Announcements -->
        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">馆内公告</h3>
          <div class="space-y-3 max-h-64 overflow-y-auto">
            <div v-for="ann in announcements" :key="ann.id" class="p-3 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
              <div class="flex items-start justify-between mb-1">
                <Badge :variant="ann.priority === 'urgent' ? 'danger' : ann.priority === 'important' ? 'warning' : 'default'" size="small">
                  {{ getPriorityLabel(ann.priority) }}
                </Badge>
                <span class="text-xs text-gray-500">{{ formatDate(ann.created_at) }}</span>
              </div>
              <div class="text-sm font-medium text-gray-900 mb-1">{{ ann.title }}</div>
              <div class="text-xs text-gray-600">{{ ann.content }}</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  BookOpenIcon,
  ClockIcon,
  ExclamationCircleIcon,
  UsersIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import { statsApi, booksApi, announcementsApi } from '@/api'

const stats = ref({})
const trends = ref([])
const popularBooks = ref([])
const categoryStats = ref([])
const announcements = ref([])

const kpiStats = computed(() => [
  { label: '馆藏图书', value: stats.value.total_books || 0, sublabel: `${stats.value.total_copies || 0} 册`, icon: BookOpenIcon, bgColor: 'bg-blue-50', iconColor: 'text-blue-600' },
  { label: '在借流通', value: stats.value.active_borrows || 0, icon: ClockIcon, bgColor: 'bg-green-50', iconColor: 'text-green-600' },
  { label: '逾期预警', value: stats.value.overdue_borrows || 0, icon: ExclamationCircleIcon, bgColor: 'bg-red-50', iconColor: 'text-red-600' },
  { label: '注册读者', value: stats.value.total_readers || 0, icon: UsersIcon, bgColor: 'bg-purple-50', iconColor: 'text-purple-600' }
])

const borrowPoints = computed(() => {
  if (!trends.value.dates) return ''
  return trends.value.dates.map((_, i) => {
    const x = (i / (trends.value.dates.length - 1)) * 400
    const max = Math.max(...trends.value.borrows, ...trends.value.returns)
    const y = 200 - ((trends.value.borrows[i] / max) * 180)
    return `${x},${y}`
  }).join(' ')
})

const borrowAreaPoints = computed(() => {
  if (!borrowPoints.value) return ''
  return `0,200 ${borrowPoints.value} 400,200`
})

const returnPoints = computed(() => {
  if (!trends.value.dates) return ''
  return trends.value.dates.map((_, i) => {
    const x = (i / (trends.value.dates.length - 1)) * 400
    const max = Math.max(...trends.value.borrows, ...trends.value.returns)
    const y = 200 - ((trends.value.returns[i] / max) * 180)
    return `${x},${y}`
  }).join(' ')
})

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const getPriorityLabel = (priority) => {
  const labels = { urgent: '紧急', important: '重要', normal: '一般' }
  return labels[priority] || '一般'
}

const loadData = async () => {
  try {
    const [statsRes, trendsRes, booksRes, annsRes] = await Promise.all([
      statsApi.getOverview(),
      statsApi.getTrends(15),
      booksApi.getPopular(8),
      announcementsApi.getActive()
    ])

    stats.value = statsRes.data
    trends.value = trendsRes.data
    popularBooks.value = booksRes.data
    announcements.value = annsRes.data

    // Calculate category stats
    if (statsRes.data.categories) {
      const total = statsRes.data.categories.reduce((sum, c) => sum + c.book_count, 0)
      categoryStats.value = statsRes.data.categories.map(c => ({
        ...c,
        percentage: total > 0 ? Math.round((c.book_count / total) * 100) : 0
      }))
    }
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
  }
}

onMounted(() => {
  loadData()
})
</script>
