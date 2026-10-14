<template>
  <div class="neo-page">
    <PageHeader title="消息通知" subtitle="到期提醒、预约到书与罚金通知">
      <template #actions>
        <Button
          variant="primary"
          :prepend-icon="CheckCircleIcon"
          :disabled="unreadCount === 0"
          :loading="markingAll"
          @click="handleMarkAllRead"
        >
          全部标记已读
        </Button>
      </template>
    </PageHeader>

    <!-- 概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <StatCard label="未读通知" :value="unreadCount" hint="建议优先处理" :icon="BellAlertIcon" tone="danger" />
      <StatCard label="今日新增" :value="todayCount" hint="今天收到的消息" :icon="SparklesIcon" tone="primary" />
      <StatCard label="通知总数" :value="totalCount" hint="最近 100 条记录" :icon="InboxStackIcon" tone="neutral" />
    </div>

    <!-- 未读 / 全部切换 -->
    <div class="mb-4">
      <Tabs v-model="activeTab" :tabs="['全部', '仅未读']" />
    </div>

    <div v-if="loading" class="py-12 text-center text-sm text-gray-500">加载中…</div>

    <Card v-else-if="visibleNotifications.length === 0" padding="normal">
      <EmptyState title="暂无通知" description="到期提醒、预约到书与罚金通知会在这里汇总。" :icon="BellIcon" />
    </Card>

    <div v-else class="space-y-4">
      <Card
        v-for="note in visibleNotifications"
        :key="note.id"
        :class="[
          'notification-card cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98]',
          note.is_read ? '' : 'notification-card-unread'
        ]"
        tabindex="0"
        role="button"
        :aria-label="`${note.title}${note.is_read ? '' : '（未读）'}`"
        @click="handleOpen(note)"
        @keydown.enter="handleCardKeydown($event, note)"
        @keydown.space="handleCardKeydown($event, note)"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <span v-if="!note.is_read" class="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" aria-hidden="true"></span>
              <Badge :variant="categoryMeta(note.category).variant" size="small">
                {{ categoryMeta(note.category).label }}
              </Badge>
              <h3 class="notification-title text-base font-semibold tracking-tight truncate">{{ note.title }}</h3>
            </div>
            <p v-if="note.content" class="notification-content text-sm mt-2">{{ note.content }}</p>
            <div class="flex items-center gap-3 mt-2">
              <span class="notification-time text-xs">{{ formatTime(note.created_at) }}</span>
              <span v-if="note.link" class="notification-link text-xs font-medium">点击查看详情</span>
            </div>
          </div>

          <div class="flex items-center gap-2 flex-shrink-0">
            <Button
              v-if="!note.is_read"
              size="small"
              variant="outline"
              @click.stop="handleMarkRead(note)"
            >
              标记已读
            </Button>
            <Button size="small" variant="ghost" @click.stop="openDeleteDialog(note)">删除</Button>
          </div>
        </div>
      </Card>
    </div>

    <!-- 删除确认 -->
    <Dialog v-model="showDeleteDialog" title="删除通知" max-width="sm">
      <p class="text-sm text-gray-600">
        确认删除通知「{{ deleteTarget?.title }}」？删除后不可恢复。
      </p>
      <template #footer>
        <Button variant="outline" @click="showDeleteDialog = false">取消</Button>
        <Button variant="danger" :loading="deleting" @click="handleDelete">确认删除</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  BellAlertIcon,
  BellIcon,
  CheckCircleIcon,
  InboxStackIcon,
  SparklesIcon
} from '@heroicons/vue/24/outline'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Tabs from '@/components/ui/Tabs.vue'
import Dialog from '@/components/ui/Dialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { notificationsApi } from '@/api'
import { notificationCategoryMeta } from '@/utils/labels'

const router = useRouter()

const allNotifications = ref([])
const unreadNotifications = ref([])
const loading = ref(false)
const markingAll = ref(false)
const activeTab = ref(0)

const showDeleteDialog = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)

const visibleNotifications = computed(() =>
  activeTab.value === 0 ? allNotifications.value : unreadNotifications.value
)
const unreadCount = computed(() => unreadNotifications.value.length)
const totalCount = computed(() => allNotifications.value.length)
const todayCount = computed(() => allNotifications.value.filter((n) => isToday(n.created_at)).length)

const categoryMeta = notificationCategoryMeta

const isToday = (dateStr) => {
  if (!dateStr) return false
  const date = new Date(dateStr)
  const now = new Date()
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  )
}

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${date.toLocaleDateString('zh-CN')} ${hh}:${mm}`
}

const loadNotifications = async () => {
  loading.value = true
  try {
    const [all, unread] = await Promise.all([
      notificationsApi.getList({ limit: 100 }),
      notificationsApi.getList({ unread_only: true, limit: 100 })
    ])
    allNotifications.value = all.data
    unreadNotifications.value = unread.data
  } catch (err) {
    window.$toast?.error('加载通知失败')
  } finally {
    loading.value = false
  }
}

const handleMarkRead = async (note) => {
  if (note.is_read) return
  try {
    await notificationsApi.markRead(note.id)
    window.$toast?.success('已标记为已读')
    await loadNotifications()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '标记已读失败')
  }
}

// 点击卡片：未读先置为已读，带跳转链接则继续导航
const handleOpen = async (note) => {
  if (!note.is_read) {
    await handleMarkRead(note)
  }
  if (note.link) {
    router.push(note.link)
  }
}

const handleCardKeydown = (event, note) => {
  // 避免内部按钮的回车冒泡触发卡片跳转
  if (event.target !== event.currentTarget) return
  event.preventDefault()
  handleOpen(note)
}

const handleMarkAllRead = async () => {
  markingAll.value = true
  try {
    const response = await notificationsApi.markAllRead()
    window.$toast?.success(response.data?.message || '已全部标记为已读')
    await loadNotifications()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '操作失败')
  } finally {
    markingAll.value = false
  }
}

const openDeleteDialog = (note) => {
  deleteTarget.value = note
  showDeleteDialog.value = true
}

const handleDelete = async () => {
  deleting.value = true
  try {
    await notificationsApi.remove(deleteTarget.value.id)
    window.$toast?.success('通知已删除')
    showDeleteDialog.value = false
    await loadNotifications()
  } catch (err) {
    window.$toast?.error(err.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  loadNotifications()
})
</script>
