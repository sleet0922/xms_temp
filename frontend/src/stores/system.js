import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/axios'

/** 后端不可用时的兜底值与 backend/config.py 保持一致 */
const FALLBACK_LIBRARY_NAME = '未来智慧云图书馆'
const FALLBACK_RULES = {
  borrow_days: 30,
  max_renew_times: 2,
  renew_days: 15,
  daily_fine_rate: '0.50',
  max_borrow_books: 8,
  reservation_expire_days: 7,
  due_reminder_days: 3
}

export const useSystemStore = defineStore('system', () => {
  const libraryName = ref(FALLBACK_LIBRARY_NAME)
  const rules = ref({ ...FALLBACK_RULES })
  const loaded = ref(false)
  let inflight = null

  /** 普通读者最大续借次数，供续借按钮禁用阈值使用 */
  const maxRenewTimes = computed(() => Number(rules.value.max_renew_times ?? 2))
  const borrowDays = computed(() => Number(rules.value.borrow_days ?? 30))

  /** 拉取公开配置（馆名 + 业务规则），失败时保留兜底值不阻断页面 */
  async function load(force = false) {
    if (loaded.value && !force) return
    if (inflight) return inflight
    inflight = api
      .get('/api/system/config')
      .then(({ data }) => {
        if (data?.library_name) libraryName.value = data.library_name
        if (data?.rules) rules.value = { ...FALLBACK_RULES, ...data.rules }
        loaded.value = true
      })
      .catch(() => {
        // 忽略：使用兜底配置
      })
      .finally(() => {
        inflight = null
      })
    return inflight
  }

  return { libraryName, rules, loaded, maxRenewTimes, borrowDays, load }
})
