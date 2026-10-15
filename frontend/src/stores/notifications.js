import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsApi } from '@/api'

// 顶栏角标与通知页共用的未读数：通知页标记已读 / 删除后直接写回，角标立即同步
export const useNotificationStore = defineStore('notifications', () => {
  const unreadCount = ref(0)

  function setUnreadCount(count) {
    unreadCount.value = Math.max(0, Number(count) || 0)
  }

  async function refreshUnreadCount() {
    try {
      const { data } = await notificationsApi.getList({ unread_only: true, limit: 200 })
      setUnreadCount(data.length)
    } catch (err) {
      // 角标失败不打断主流程
    }
  }

  return { unreadCount, setUnreadCount, refreshUnreadCount }
})
