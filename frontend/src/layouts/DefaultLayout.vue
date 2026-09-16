<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 移动端遮罩 -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-30 bg-gray-900/50 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- 侧边栏 -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-40 w-64 bg-gray-900 transform transition-transform duration-200 ease-in-out lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
    >
      <div class="flex flex-col h-full">
        <!-- Logo -->
        <div class="flex items-center gap-3 px-6 h-16 border-b border-gray-800">
          <component :is="getIconComponent('mdi-library')" class="w-8 h-8 text-blue-400" />
          <div>
            <div class="text-white font-bold leading-tight">智慧云图书馆</div>
            <div class="text-gray-400 text-xs">Library Management</div>
          </div>
        </div>

        <!-- 菜单 -->
        <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          <RouterLink
            v-for="item in visibleMenu"
            :key="item.path"
            :to="item.path"
            @click="sidebarOpen = false"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isActive(item.path)
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            ]"
          >
            <component :is="getIconComponent(item.icon)" class="w-5 h-5 flex-shrink-0" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>

        <!-- 底部用户信息 -->
        <div class="border-t border-gray-800 p-4">
          <RouterLink
            to="/profile"
            @click="sidebarOpen = false"
            class="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <div class="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold flex-shrink-0">
              {{ userInitial }}
            </div>
            <div class="min-w-0">
              <div class="text-sm text-white font-medium truncate">{{ userStore.user?.full_name || userStore.user?.username }}</div>
              <div class="text-xs text-gray-400">{{ roleLabel }}</div>
            </div>
          </RouterLink>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="lg:pl-64 flex flex-col min-h-screen">
      <!-- 顶栏 -->
      <header class="sticky top-0 z-20 h-16 bg-white border-b border-gray-200 flex items-center gap-4 px-4 sm:px-6">
        <button
          class="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
          @click="sidebarOpen = true"
        >
          <component :is="getIconComponent('mdi-menu')" class="w-6 h-6" />
        </button>

        <h1 class="text-lg font-semibold text-gray-900 truncate">{{ route.meta.title || '' }}</h1>

        <div class="ml-auto flex items-center gap-3">
          <span class="hidden sm:inline-flex px-2.5 py-1 rounded-full text-xs font-medium" :class="roleBadgeClass">
            {{ roleLabel }}
          </span>
          <span class="hidden sm:block text-sm text-gray-700">{{ userStore.user?.full_name || userStore.user?.username }}</span>
          <button
            class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-red-600 transition-colors"
            title="退出登录"
            @click="handleLogout"
          >
            <component :is="getIconComponent('mdi-logout')" class="w-5 h-5" />
          </button>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="flex-1">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getIconComponent } from '@/utils/iconMap'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const sidebarOpen = ref(false)

const menuItems = [
  { path: '/', label: '全馆仪表盘', icon: 'mdi-view-dashboard-outline' },
  { path: '/books', label: '书目大厅', icon: 'mdi-book-search-outline' },
  { path: '/circulation', label: '借还服务台', icon: 'mdi-barcode-scan', role: 'librarian' },
  { path: '/borrows', label: '借阅中心', icon: 'mdi-book-clock-outline' },
  { path: '/reservations', label: '预约排队', icon: 'mdi-calendar-clock-outline' },
  { path: '/fines', label: '罚金中心', icon: 'mdi-cash-multiple' },
  { path: '/readers', label: '读者档案', icon: 'mdi-account-group', role: 'librarian' },
  { path: '/analytics', label: '统计报表', icon: 'mdi-chart-box-outline' },
  { path: '/settings', label: '系统设置', icon: 'mdi-cog-outline', role: 'admin' }
]

const visibleMenu = computed(() => menuItems.filter(item => {
  if (item.role === 'admin') return userStore.isAdmin
  if (item.role === 'librarian') return userStore.isLibrarian
  return true
}))

const roleLabel = computed(() => ({
  admin: '管理员',
  librarian: '馆员',
  reader: '读者'
}[userStore.user?.role] || '用户'))

const roleBadgeClass = computed(() => ({
  admin: 'bg-purple-100 text-purple-700',
  librarian: 'bg-blue-100 text-blue-700',
  reader: 'bg-green-100 text-green-700'
}[userStore.user?.role] || 'bg-gray-100 text-gray-700'))

const userInitial = computed(() => {
  const name = userStore.user?.full_name || userStore.user?.username || '?'
  return name.charAt(0).toUpperCase()
})

function isActive(path) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>
