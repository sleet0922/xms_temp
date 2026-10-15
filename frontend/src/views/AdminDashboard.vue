<template>
  <div class="neo-page">
    <PageHeader title="后台概览" subtitle="馆藏、用户与流通数据总览">
      <template #actions>
        <Button variant="outline" :prepend-icon="ArrowPathIcon" :loading="loading" @click="loadOverview">刷新数据</Button>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard v-for="stat in stats" :key="stat.label" :label="stat.label" :value="stat.value" :hint="stat.hint" :icon="stat.icon" :tone="stat.tone" />
    </div>

    <section class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[1.15fr_0.85fr]">
      <Card>
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-base font-medium text-gray-900">常用操作</h2>
            
          </div>
        </div>
        <div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <RouterLink v-for="action in actions" :key="action.to" :to="action.to" class="admin-action-card">
            <div class="admin-action-icon"><component :is="action.icon" class="h-5 w-5" /></div>
            <div>
              <div class="font-medium text-gray-900">{{ action.label }}</div>
              <div class="mt-1 text-xs text-gray-500">{{ action.description }}</div>
            </div>
            <component :is="ChevronRightIcon" class="ml-auto h-4 w-4 text-gray-400" />
          </RouterLink>
        </div>
      </Card>

      <Card>
        <h2 class="text-base font-medium text-gray-900">流通状态</h2>
        <dl class="mt-4 divide-y divide-gray-200 text-sm">
          <div v-for="row in statusRows" :key="row.label" class="flex items-center justify-between py-3 first:pt-0 last:pb-0">
            <dt class="text-gray-600">{{ row.label }}</dt>
            <dd class="font-medium tabular-nums" :class="row.tone">{{ row.value }}</dd>
          </div>
        </dl>
      </Card>
    </section>

    <section class="mt-4">
      <Card>
        <div class="flex items-center justify-between">
          <h2 class="text-base font-medium text-gray-900">热门图书</h2>
          <RouterLink to="/admin/analytics" class="text-sm text-[#2f5b4e] hover:text-[#487a69]">完整报表</RouterLink>
        </div>
        <ol v-if="popular.length" class="mt-4 space-y-3">
          <li v-for="(book, index) in popular" :key="book.id" class="flex items-center gap-3">
            <span
              class="inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded text-xs font-semibold"
              :class="index < 3 ? 'bg-[#2f5b4e] text-white' : 'bg-[#f2f3f5] text-gray-500'"
            >{{ index + 1 }}</span>
            <RouterLink :to="`/admin/books/${book.id}`" class="min-w-0 flex-1 truncate text-sm text-gray-900 hover:text-[#2f5b4e]">{{ book.title }}</RouterLink>
            <span class="flex-shrink-0 text-xs tabular-nums text-gray-500">{{ book.borrow_count }} 次</span>
          </li>
        </ol>
        <p v-else class="py-16 text-center text-sm text-gray-500">暂无借阅排行</p>
      </Card>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowPathIcon, ChevronRightIcon, BookOpenIcon, ChartBarIcon, CurrencyDollarIcon, UserGroupIcon } from '@heroicons/vue/24/outline'
import { statsApi } from '@/api'
import PageHeader from '@/components/ui/PageHeader.vue'
import Card from '@/components/ui/Card.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Button from '@/components/ui/Button.vue'

const overview = ref({})
const loading = ref(false)
const popular = ref([])


const stats = computed(() => [
  { label: '馆藏图书', value: overview.value.total_books ?? 0, hint: `${overview.value.total_copies ?? 0} 册含复本`, icon: BookOpenIcon, tone: 'primary' },
  { label: '注册用户', value: overview.value.total_readers ?? 0, hint: '读者账号总数', icon: UserGroupIcon, tone: 'success' },
  { label: '当前借阅', value: overview.value.active_borrows ?? 0, hint: `${overview.value.overdue_borrows ?? 0} 条逾期`, icon: ChartBarIcon, tone: 'warning' },
  { label: '待处理罚金', value: `¥${Number(overview.value.unpaid_fines ?? 0).toFixed(2)}`, hint: '逾期与赔偿账单', icon: CurrencyDollarIcon, tone: 'danger' }
])

const actions = [
  { to: '/admin/books', label: '维护馆藏', description: '新增书目、补录复本与检索', icon: BookOpenIcon },
  { to: '/admin/readers', label: '管理用户', description: '读者档案、状态与借阅画像', icon: UserGroupIcon },
  { to: '/admin/circulation', label: '处理借还', description: '扫码借书、还书与续借', icon: ChartBarIcon },
  { to: '/admin/analytics', label: '查看报表', description: '流通趋势与馆藏结构', icon: ArrowPathIcon }
]

const statusRows = computed(() => [
  { label: '馆藏复本', value: `${overview.value.total_copies ?? 0} 册`, tone: 'text-gray-900' },
  { label: '在借中', value: `${overview.value.active_borrows ?? 0} 条`, tone: 'text-gray-900' },
  { label: '已逾期', value: `${overview.value.overdue_borrows ?? 0} 条`, tone: (overview.value.overdue_borrows ?? 0) > 0 ? 'text-[#b42318]' : 'text-gray-900' },
  { label: '未缴罚金', value: `¥${Number(overview.value.unpaid_fines ?? 0).toFixed(2)}`, tone: 'text-gray-900' }
])

async function loadOverview() {
  loading.value = true
  try {
    const [overviewRes, popularRes] = await Promise.allSettled([
      statsApi.getOverview(),
      statsApi.getPopularBooks(6)
    ])
    if (overviewRes.status === 'fulfilled') overview.value = overviewRes.value.data || {}
    if (popularRes.status === 'fulfilled') popular.value = popularRes.value.data || []
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>
