import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { normalizeErrorDetail, shouldRedirectToLogin } from '@/api/axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    normalizeErrorDetail(error)
    if (shouldRedirectToLogin(error)) {
      const userStore = useUserStore()
      userStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  updateProfile: (data) => api.put('/auth/profile', data),
  changePassword: (oldPassword, newPassword) =>
    api.put('/auth/change-password', { old_password: oldPassword, new_password: newPassword })
}

// Stats API
export const statsApi = {
  getOverview: () => api.get('/stats/overview'),
  getTrends: (days) => api.get(`/stats/trends?days=${days}`),
  getCategories: () => api.get('/stats/categories'),
  getPopularBooks: (limit = 8) => api.get(`/stats/popular-books?limit=${limit}`),
  getTopRated: (limit = 8) => api.get(`/stats/top-rated?limit=${limit}`),
  getFormats: () => api.get('/stats/formats'),
  getLanguages: () => api.get('/stats/languages'),
  getActiveReaders: (limit = 10) => api.get(`/stats/active-readers?limit=${limit}`)
}

// Books API
export const booksApi = {
  getList: (params) => api.get('/books', { params }),
  getFacets: () => api.get('/books/facets'),
  getById: (id) => api.get(`/books/${id}`),
  getSimilar: (id, limit = 6) => api.get(`/books/${id}/similar?limit=${limit}`),
  create: (data, copiesCount = 1) => api.post('/books', data, { params: { copies_count: copiesCount } }),
  update: (id, data) => api.put(`/books/${id}`, data),
  delete: (id) => api.delete(`/books/${id}`),
  addCopy: (id, data) => api.post(`/books/${id}/copies`, data),
  getPopular: (limit) => api.get(`/stats/popular-books?limit=${limit}`),
  export: () => api.get('/books-export', { responseType: 'blob' })
}

// Reviews API
export const reviewsApi = {
  getByBook: (bookId, includeHidden = false) =>
    api.get(`/books/${bookId}/reviews?include_hidden=${includeHidden}`),
  upsert: (bookId, data) => api.post(`/books/${bookId}/reviews`, data),
  getMine: () => api.get('/reviews/my'),
  getAll: (params) => api.get('/reviews', { params }),
  update: (id, data) => api.put(`/reviews/${id}`, data),
  setVisibility: (id, isHidden) => api.put(`/reviews/${id}/visibility`, { is_hidden: isHidden }),
  remove: (id) => api.delete(`/reviews/${id}`)
}

// Recommendations API
export const recommendApi = {
  getList: (limit = 8) => api.get(`/recommendations?limit=${limit}`)
}

// Notifications API
export const notificationsApi = {
  getList: (params) => api.get('/notifications', { params }),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
  remove: (id) => api.delete(`/notifications/${id}`)
}

// Circulation API
export const circulationApi = {
  // 借书：传 barcode（扫实体册）或 book_id（按书目自动分配在架复本）
  borrow: (data) => api.post('/circulation/borrow', data),
  // 还书：传 barcode（扫实体册）或 record_id（按借阅记录归还）
  return: (data) => api.post('/circulation/return', data),
  approveReturnRequest: (id) => api.post(`/circulation/return-requests/${id}/approve`),
  rejectReturnRequest: (id) => api.post(`/circulation/return-requests/${id}/reject`),
  renew: (recordId) => api.post(`/circulation/renew/${recordId}`)
}

// Borrows API
export const borrowsApi = {
  getList: (params) => api.get('/borrows', { params }),
  getMyBorrows: () => api.get('/borrows/my'),
  renewBorrow: (id) => api.post(`/circulation/renew/${id}`),
  selfBorrow: (bookId) => api.post('/borrows/self', { book_id: bookId }),
  requestReturn: (id) => api.post(`/borrows/${id}/return-request`)
}

// Readers API
export const readersApi = {
  getList: (params) => api.get('/readers', { params }),
  getOverview: (id) => api.get(`/readers/${id}/overview`),
  create: (data) => api.post('/readers', data),
  update: (id, data) => api.put(`/readers/${id}`, data),
  resetPassword: (id) => api.post(`/readers/${id}/reset-password`)
}

// Fines API
export const finesApi = {
  getList: (params) => api.get('/fines', { params }),
  getSummary: () => api.get('/fines/summary'),
  settle: (id, data) => api.post(`/fines/${id}/pay`, data),
  remind: (readerId) => api.post(`/fines/remind/${readerId}`)
}

// Reservations API
export const reservationsApi = {
  getList: () => api.get('/reservations'),
  create: (bookId) => api.post('/reservations', { book_id: bookId }),
  cancel: (id) => api.post(`/reservations/${id}/cancel`),
  // 预约取书：馆员为读者办理借出并兑现预约
  fulfill: (id) => api.post(`/reservations/${id}/fulfill`)
}

// Announcements API
export const announcementsApi = {
  getActive: () => api.get('/announcements'),
  create: (data) => api.post('/announcements', data),
  delete: (id) => api.delete(`/announcements/${id}`)
}

// System API（管理员）
export const systemApi = {
  // 公开配置（馆名 + 业务规则），无需登录
  getConfig: () => api.get('/system/config'),
  getInfo: () => api.get('/system/info'),
  getSettings: () => api.get('/settings'),
  updateSetting: (key, value) => api.put(`/settings/${key}`, { setting_value: value }),
  getAuditLogs: (params) => api.get('/audit-logs', { params })
}

// Categories & Locations API
export const categoriesApi = {
  getAll: () => api.get('/categories'),
  create: (data) => api.post('/categories', data)
}

export const locationsApi = {
  getAll: () => api.get('/shelf-locations'),
  create: (data) => api.post('/shelf-locations', data)
}

export default api
