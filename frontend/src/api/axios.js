import axios from 'axios'
import { formatErrorDetail } from '@/utils/errors'

const api = axios.create({
  baseURL: '',
  timeout: 10000
})

// 422 校验错误的 detail 是对象数组，统一转成中文字符串，页面直接展示即可
export function normalizeErrorDetail(error) {
  const data = error.response?.data
  if (data && typeof data === 'object' && data.detail && typeof data.detail !== 'string') {
    data.detail = formatErrorDetail(data.detail) || undefined
  }
}

// 登录接口本身返回 401 表示用户名或密码错误，应留在登录页展示提示，而不是整页刷新
export function shouldRedirectToLogin(error) {
  if (error.response?.status !== 401) return false
  const url = error.config?.url || ''
  return !url.endsWith('/auth/login')
}

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    normalizeErrorDetail(error)
    if (shouldRedirectToLogin(error)) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
