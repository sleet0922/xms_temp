/**
 * 共享展示标签：语种 / 通知分类 / 预约状态
 *
 * 注意：通知分类的键必须与后端 services/notify.py 实际发出的 category 一致，
 * 否则会退化成显示英文原文。
 */

const LANGUAGE_NAMES = {
  zh: '中文',
  en: '英文',
  ja: '日文',
  ko: '韩文',
  fr: '法文',
  de: '德文',
  ru: '俄文',
  es: '西班牙文'
}

/** 语种代码 → 中文名；后端若已返回中文则原样保留 */
export const languageLabel = (code) => LANGUAGE_NAMES[code] || code || '-'

/** 通知分类 → 中文标签与语义色（键与后端 notify.py 对齐） */
export const NOTIFICATION_CATEGORY_META = {
  due_reminder: { label: '到期提醒', variant: 'primary' },
  overdue: { label: '逾期预警', variant: 'warning' },
  reservation_ready: { label: '预约到书', variant: 'success' },
  reservation_fulfilled: { label: '预约已兑现', variant: 'success' },
  fine: { label: '罚金通知', variant: 'danger' },
  return_request: { label: '还书申请', variant: 'warning' },
  return_request_approved: { label: '还书已确认', variant: 'success' },
  return_request_rejected: { label: '还书被驳回', variant: 'danger' },
  system: { label: '系统消息', variant: 'default' },
  // 兼容早期缩写键，保证历史数据也能正确显示
  due: { label: '到期提醒', variant: 'primary' },
  reservation: { label: '预约到书', variant: 'success' }
}

// 未登记的新分类统一显示「通知」，不把内部英文键直接展示给用户
export const notificationCategoryMeta = (category) =>
  NOTIFICATION_CATEGORY_META[category] || { label: '通知', variant: 'default' }

/** 预约状态 → 中文标签与语义色 */
export const RESERVATION_STATUS_META = {
  waiting: { label: '等待中', variant: 'warning' },
  notified: { label: '已到馆', variant: 'primary' },
  fulfilled: { label: '已兑现', variant: 'success' },
  cancelled: { label: '已取消', variant: 'default' }
}

export const reservationStatusLabel = (status) =>
  RESERVATION_STATUS_META[status]?.label || status

export const reservationStatusVariant = (status) =>
  RESERVATION_STATUS_META[status]?.variant || 'default'

/** 预约是否仍在进行中 */
export const isActiveReservation = (status) => ['waiting', 'notified'].includes(status)
