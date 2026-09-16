import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/axios'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isLibrarian = computed(() => user.value?.role === 'admin' || user.value?.role === 'librarian')
  const isReader = computed(() => user.value?.role === 'reader')

  async function login(username, password) {
    const response = await api.post('/api/auth/login', { username, password })
    token.value = response.data.access_token
    user.value = response.data.user
    localStorage.setItem('token', token.value)
    return response.data
  }

  async function register(userData) {
    return await api.post('/api/auth/register', userData)
  }

  async function fetchUserInfo() {
    if (!token.value) return
    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  // 用户信息由路由守卫在首次导航时按需拉取（保证角色判定发生在数据就绪之后），此处不再重复请求

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isLibrarian,
    isReader,
    login,
    register,
    logout,
    fetchUserInfo
  }
})
