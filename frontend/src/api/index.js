import axios from 'axios'
import { useUserStore } from '@/stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
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
    if (error.response?.status === 401) {
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
  changePassword: (oldPassword, newPassword) =>
    api.put('/auth/change-password', { old_password: oldPassword, new_password: newPassword })
}

// Stats API
export const statsApi = {
  getOverview: () => api.get('/stats/overview'),
  getTrends: (days) => api.get(`/stats/trends?days=${days}`),
  getCategories: () => api.get('/stats/categories')
}

// Books API
export const booksApi = {
  getList: (params) => api.get('/books', { params }),
  getById: (id) => api.get(`/books/${id}`),
  create: (data) => api.post('/books', data),
  update: (id, data) => api.put(`/books/${id}`, data),
  delete: (id) => api.delete(`/books/${id}`),
  getPopular: (limit) => api.get(`/stats/popular-books?limit=${limit}`),
  export: () => api.get('/books-export', { responseType: 'blob' })
}

// Circulation API
export const circulationApi = {
  borrow: (cardNumber, barcode) => api.post('/circulation/borrow', { card_number: cardNumber, barcode }),
  return: (barcode) => api.post('/circulation/return', { barcode })
}

// Borrows API
export const borrowsApi = {
  getList: (params) => api.get('/borrows', { params }),
  getMyBorrows: () => api.get('/borrows/my'),
  renewBorrow: (id) => api.post(`/circulation/renew/${id}`)
}

// Readers API
export const readersApi = {
  getList: (params) => api.get('/readers', { params }),
  create: (data) => api.post('/readers', data),
  update: (id, data) => api.put(`/readers/${id}`, data),
  resetPassword: (id) => api.post(`/readers/${id}/reset-password`)
}

// Fines API
export const finesApi = {
  getList: (params) => api.get('/fines', { params }),
  settle: (id, data) => api.post(`/fines/${id}/pay`, data)
}

// Reservations API
export const reservationsApi = {
  getList: () => api.get('/reservations'),
  create: (data) => api.post('/reservations', data),
  cancel: (id) => api.post(`/reservations/${id}/cancel`)
}

// Announcements API
export const announcementsApi = {
  getActive: () => api.get('/announcements'),
  create: (data) => api.post('/announcements', data),
  delete: (id) => api.delete(`/announcements/${id}`)
}

// Settings API
export const settingsApi = {
  getAll: () => api.get('/settings'),
  update: (key, value) => api.put(`/settings/${key}`, { setting_value: value })
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
