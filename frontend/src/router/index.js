import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSystemStore } from '@/stores/system'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'

const userRoutes = [
  { path: '', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '我的图书馆' } },
  { path: 'books', name: 'Books', component: () => import('@/views/Books.vue'), meta: { title: '馆藏检索' } },
  { path: 'books/:id', name: 'BookDetail', component: () => import('@/views/BookDetail.vue'), meta: { title: '图书详情' } },
  { path: 'shelf', name: 'MyShelf', component: () => import('@/views/MyShelf.vue'), meta: { title: '我的书架' } },
  { path: 'borrows', name: 'Borrows', component: () => import('@/views/Borrows.vue'), meta: { title: '借阅记录' } },
  { path: 'reservations', name: 'Reservations', component: () => import('@/views/Reservations.vue'), meta: { title: '预约排队' } },
  { path: 'fines', name: 'Fines', component: () => import('@/views/Fines.vue'), meta: { title: '罚金中心' } },
  { path: 'notifications', name: 'Notifications', component: () => import('@/views/Notifications.vue'), meta: { title: '消息通知' } },
  { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue'), meta: { title: '个人中心' } }
]

const adminRoutes = [
  { path: '', name: 'AdminDashboard', component: () => import('@/views/AdminDashboard.vue'), meta: { title: '后台概览' } },
  { path: 'books', name: 'AdminBooks', component: () => import('@/views/Books.vue'), meta: { title: '馆藏与书目' } },
  { path: 'books/:id', name: 'AdminBookDetail', component: () => import('@/views/BookDetail.vue'), meta: { title: '书目详情' } },
  { path: 'readers', name: 'AdminReaders', component: () => import('@/views/Readers.vue'), meta: { title: '用户管理' } },
  { path: 'circulation', name: 'AdminCirculation', component: () => import('@/views/Circulation.vue'), meta: { title: '借还工作台' } },
  { path: 'borrows', name: 'AdminBorrows', component: () => import('@/views/Borrows.vue'), meta: { title: '借阅记录' } },
  { path: 'fines', name: 'AdminFines', component: () => import('@/views/Fines.vue'), meta: { title: '罚金处理' } },
  { path: 'analytics', name: 'AdminAnalytics', component: () => import('@/views/Analytics.vue'), meta: { title: '统计报表' } },
  { path: 'settings', name: 'AdminSettings', component: () => import('@/views/Settings.vue'), meta: { title: '系统设置', role: 'admin' } }
]

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { requiresAuth: false, title: '登录' } },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue'), meta: { requiresAuth: false, title: '读者注册' } },
  { path: '/', component: DefaultLayout, meta: { requiresAuth: true, audience: 'user' }, children: userRoutes },
  { path: '/admin', component: AdminLayout, meta: { requiresAuth: true, audience: 'admin', role: 'librarian' }, children: adminRoutes }
]

const router = createRouter({ history: createWebHistory(), routes })

function homeFor(userStore) {
  return userStore.isLibrarian ? '/admin' : '/'
}

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const systemStore = useSystemStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (!systemStore.loaded) await systemStore.load()
  if (to.meta.title) document.title = `${to.meta.title} - ${systemStore.libraryName}`

  if (requiresAuth && !userStore.isAuthenticated) {
    next('/login')
    return
  }

  if (userStore.isAuthenticated && !userStore.user) await userStore.fetchUserInfo()

  if (requiresAuth && !userStore.isAuthenticated) {
    next('/login')
  } else if (!requiresAuth && userStore.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    next(homeFor(userStore))
  } else if (to.meta.audience === 'admin' && !userStore.isLibrarian) {
    next('/')
  } else if (to.meta.role === 'admin' && !userStore.isAdmin) {
    next('/admin')
  } else {
    next()
  }
})

export default router
