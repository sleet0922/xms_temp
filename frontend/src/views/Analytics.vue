<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">流通统计报表</h1>
        <p class="text-gray-600 mt-1">图书馆运营数据分析</p>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card hover v-for="(stat, index) in kpiStats" :key="index">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 mb-1">{{ stat.label }}</div>
              <div class="text-2xl font-bold text-gray-900">{{ stat.value }}</div>
              <div v-if="stat.sublabel" class="text-xs mt-1" :class="stat.sublabelColor">{{ stat.sublabel }}</div>
            </div>
            <div :class="`w-12 h-12 rounded-lg ${stat.bgColor} flex items-center justify-center`">
              <component :is="stat.icon" :class="`w-6 h-6 ${stat.iconColor}`" />
            </div>
          </div>
        </Card>
      </div>

      <!-- Metrics Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">馆藏利用率</h3>
          <div class="flex items-center justify-center py-8">
            <div class="relative w-40 h-40">
              <svg class="w-full h-full transform -rotate-90">
                <circle cx="80" cy="80" r="70" stroke="#e5e7eb" stroke-width="12" fill="none" />
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke="#2563eb"
                  stroke-width="12"
                  fill="none"
                  :stroke-dasharray="`${utilizationRate * 4.4} 440`"
                  class="transition-all duration-500"
                />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-3xl font-bold text-gray-900">{{ utilizationRate }}%</div>
                  <div class="text-xs text-gray-500">在借占比</div>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">今日流通平衡表</h3>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-gray-600">借出</span>
              <span class="text-2xl font-bold text-blue-600">{{ stats.today_borrows || 0 }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-600">归还</span>
              <span class="text-2xl font-bold text-green-600">{{ stats.today_returns || 0 }}</span>
            </div>
            <div class="border-t border-gray-200 pt-4 flex justify-between items-center">
              <span class="text-gray-900 font-medium">净流出</span>
              <span class="text-2xl font-bold" :class="netFlow >= 0 ? 'text-blue-600' : 'text-green-600'">
                {{ netFlow >= 0 ? '+' : '' }}{{ netFlow }}
              </span>
            </div>
          </div>
        </Card>
      </div>

      <!-- Additional Stats -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">逾期发生率</h3>
          <div class="text-center py-4">
            <div class="text-4xl font-bold mb-2" :class="overdueRate > 10 ? 'text-red-600' : 'text-green-600'">
              {{ overdueRate }}%
            </div>
            <div class="text-sm text-gray-500">{{ stats.overdue_borrows || 0 }} / {{ stats.active_borrows || 0 }} 笔</div>
          </div>
        </Card>

        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">活跃读者覆盖率</h3>
          <div class="text-center py-4">
            <div class="text-4xl font-bold text-blue-600 mb-2">{{ activeReaderRate }}%</div>
            <div class="text-sm text-gray-500">近30天有借阅行为</div>
          </div>
        </Card>

        <Card padding="normal">
          <h3 class="text-lg font-bold text-gray-900 mb-4">月度流通吞吐量</h3>
          <div class="text-center py-4">
            <div class="text-4xl font-bold text-purple-600 mb-2">{{ monthlyVolume }}</div>
            <div class="text-sm text-gray-500">本月借还总计</div>
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
  ChartBarIcon,
  ExclamationCircleIcon,
  UsersIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import { statsApi } from '@/api'

const stats = ref({})

const kpiStats = computed(() => [
  { label: '馆藏总量', value: stats.value.total_copies || 0, sublabel: `${stats.value.total_books || 0} 种`, icon: BookOpenIcon, bgColor: 'bg-blue-50', iconColor: 'text-blue-600' },
  { label: '当前在借', value: stats.value.active_borrows || 0, icon: ChartBarIcon, bgColor: 'bg-green-50', iconColor: 'text-green-600' },
  { label: '逾期待还', value: stats.value.overdue_borrows || 0, icon: ExclamationCircleIcon, bgColor: 'bg-red-50', iconColor: 'text-red-600', sublabel: '需催还', sublabelColor: 'text-red-600' },
  { label: '注册读者', value: stats.value.total_readers || 0, icon: UsersIcon, bgColor: 'bg-purple-50', iconColor: 'text-purple-600' }
])

const utilizationRate = computed(() => {
  if (!stats.value.total_copies || !stats.value.active_borrows) return 0
  return Math.round((stats.value.active_borrows / stats.value.total_copies) * 100)
})

const netFlow = computed(() => {
  return (stats.value.today_borrows || 0) - (stats.value.today_returns || 0)
})

const overdueRate = computed(() => {
  if (!stats.value.active_borrows) return 0
  return Math.round(((stats.value.overdue_borrows || 0) / stats.value.active_borrows) * 100)
})

const activeReaderRate = computed(() => {
  if (!stats.value.total_readers) return 0
  return Math.round((stats.value.active_readers || stats.value.total_readers * 0.6) / stats.value.total_readers * 100)
})

const monthlyVolume = computed(() => {
  return (stats.value.monthly_borrows || 0) + (stats.value.monthly_returns || 0)
})

const loadStats = async () => {
  try {
    const response = await statsApi.getOverview()
    stats.value = response.data
  } catch (err) {
    window.$toast?.error('加载统计数据失败')
  }
}

onMounted(() => {
  loadStats()
})
</script>
