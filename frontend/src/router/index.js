import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, title: '登录 - 智慧云图书馆' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false, title: '读者注册' }
  },
  {
    path: '/',
    component: DefaultLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { requiresAuth: true, title: '全馆仪表盘' }
      },
      {
        path: 'books',
        name: 'Books',
        component: () => import('@/views/Books.vue'),
        meta: { requiresAuth: true, title: '书目大厅与编目' }
      },
      {
        path: 'books/:id',
        name: 'BookDetail',
        component: () => import('@/views/BookDetail.vue'),
        meta: { requiresAuth: true, title: '图书详情' }
      },
      {
        path: 'shelf',
        name: 'MyShelf',
        component: () => import('@/views/MyShelf.vue'),
        meta: { requiresAuth: true, title: '我的书架' }
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/Notifications.vue'),
        meta: { requiresAuth: true, title: '消息通知中心' }
      },
      {
        path: 'circulation',
        name: 'Circulation',
        component: () => import('@/views/Circulation.vue'),
        meta: { requiresAuth: true, role: 'librarian', title: '智慧借还服务台' }
      },
      {
        path: 'borrows',
        name: 'Borrows',
        component: () => import('@/views/Borrows.vue'),
        meta: { requiresAuth: true, title: '借阅流转中心' }
      },
      {
        path: 'reservations',
        name: 'Reservations',
        component: () => import('@/views/Reservations.vue'),
        meta: { requiresAuth: true, title: '图书预约排队' }
      },
      {
        path: 'fines',
        name: 'Fines',
        component: () => import('@/views/Fines.vue'),
        meta: { requiresAuth: true, title: '罚金账务中心' }
      },
      {
        path: 'readers',
        name: 'Readers',
        component: () => import('@/views/Readers.vue'),
        meta: { requiresAuth: true, role: 'librarian', title: '读者档案管理' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: { requiresAuth: true, title: '流通统计报表' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { requiresAuth: true, role: 'admin', title: '系统设置与审计' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { requiresAuth: true, title: '个人中心与借书卡' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (to.meta.title) {
    document.title = to.meta.title
  }

  if (requiresAuth && !userStore.isAuthenticated) {
    next('/login')
    return
  }

  // 刷新页面时令牌已存在但用户信息尚未拉取，先补齐再判定角色，避免误重定向
  if (userStore.isAuthenticated && !userStore.user) {
    await userStore.fetchUserInfo()
  }

  if (requiresAuth && !userStore.isAuthenticated) {
    next('/login')
  } else if (!requiresAuth && userStore.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    next('/')
  } else if (to.meta.role === 'admin' && !userStore.isAdmin) {
    next('/')
  } else if (to.meta.role === 'librarian' && !userStore.isLibrarian) {
    next('/')
  } else {
    next()
  }
})

export default router
