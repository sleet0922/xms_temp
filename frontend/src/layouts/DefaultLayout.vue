<template>
  <div class="neo-shell min-h-screen">
    <!-- 移动端遮罩 -->
    <div
      v-if="sidebarOpen"
      class="neo-dialog-backdrop fixed inset-0 z-30 lg:hidden transition-opacity duration-200"
      @click="sidebarOpen = false"
    ></div>

    <!-- 侧边栏 -->
    <aside
      :class="[
        'neo-sidebar fixed inset-y-0 left-0 z-40 w-64 border-r border-gray-200 transform transition-transform duration-200 ease-out lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
    >
      <div class="flex flex-col h-full">
        <!-- Logo -->
        <RouterLink to="/" class="flex items-center gap-3 px-6 h-16 border-b border-gray-200 group">
          <div class="neo-brand-mark w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-200 ease-out group-hover:scale-105">
            <component :is="getIconComponent('mdi-library')" class="w-5 h-5 text-[#2f6f68] transition-colors duration-200" />
          </div>
          <div class="min-w-0">
            <div class="text-gray-900 font-semibold tracking-tight leading-tight truncate">智慧云图书馆</div>
            <div class="text-gray-500 text-xs">Library Management</div>
          </div>
        </RouterLink>

        <!-- 菜单 -->
        <nav class="flex-1 overflow-y-auto scrollbar-thin py-4 px-3 space-y-1">
          <template v-for="item in visibleMenu" :key="item.path">
            <div v-if="item.group" class="px-3 pt-4 pb-1 text-xs font-medium text-gray-400 uppercase tracking-wide">
              {{ item.group }}
            </div>
            <RouterLink
              v-else
              :to="item.path"
              @click="sidebarOpen = false"
              :class="[
                'neo-nav-item flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 active:scale-[0.98]',
                isActive(item.path)
                  ? 'is-active'
                  : ''
              ]"
            >
              <component :is="getIconComponent(item.icon)" class="w-5 h-5 flex-shrink-0" />
              <span class="truncate">{{ item.label }}</span>
              <span
                v-if="item.path === '/notifications' && unreadCount > 0"
                class="ml-auto inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 rounded-full bg-red-500 text-white text-xs font-semibold"
              >
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </RouterLink>
          </template>
        </nav>

        <!-- 底部用户信息 -->
          <div class="border-t border-gray-200 p-4">
          <RouterLink
            to="/profile"
            @click="sidebarOpen = false"
            class="flex items-center gap-3 px-2 py-2 rounded-lg transition-colors duration-150 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
          >
            <div class="neo-user-orb w-10 h-10 rounded-2xl flex items-center justify-center font-semibold flex-shrink-0">
              {{ userInitial }}
            </div>
            <div class="min-w-0">
              <div class="text-sm text-gray-900 font-medium truncate">{{ userStore.user?.full_name || userStore.user?.username }}</div>
              <div class="text-xs text-gray-500">{{ roleLabel }}</div>
            </div>
          </RouterLink>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="lg:pl-64 flex flex-col min-h-screen">
      <!-- 顶栏 -->
      <header class="neo-header sticky top-0 z-20 h-[76px] border-b flex items-center gap-4 px-4 sm:px-6">
        <button
          type="button"
          aria-label="打开导航菜单"
          class="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors duration-150 active:scale-[0.98]"
          @click="sidebarOpen = true"
        >
          <component :is="getIconComponent('mdi-menu')" class="w-6 h-6" />
        </button>

        <div class="min-w-0">
          <h1 class="text-lg font-semibold tracking-tight text-gray-900 truncate">{{ route.meta.title || '' }}</h1>
        </div>

        <div class="ml-auto flex items-center gap-2 sm:gap-3">
          <span class="neo-role-badge hidden sm:inline-flex px-2.5 py-1 rounded-lg text-xs font-medium" :class="roleBadgeClass">
            {{ roleLabel }}
          </span>

          <!-- 通知铃铛 -->
          <RouterLink
            to="/notifications"
            aria-label="消息通知"
            class="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors duration-150 active:scale-[0.98]"
            title="消息通知"
          >
            <component :is="getIconComponent('mdi-bell-outline')" class="w-5 h-5" />
            <span
              v-if="unreadCount > 0"
              class="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-red-500 text-white text-[10px] font-semibold"
            >
              {{ unreadCount > 99 ? '99+' : unreadCount }}
            </span>
          </RouterLink>

          <div class="hidden sm:block text-sm text-gray-700 max-w-[10rem] truncate">
            {{ userStore.user?.full_name || userStore.user?.username }}
          </div>

          <button
            type="button"
            class="p-2 rounded-lg text-gray-500 hover:bg-red-50 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors duration-150 active:scale-[0.98]"
            title="退出登录"
            @click="handleLogout"
          >
            <component :is="getIconComponent('mdi-logout')" class="w-5 h-5" />
          </button>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="flex-1">
        <RouterView v-slot="{ Component, route: renderedRoute }">
          <Transition name="page-transition" mode="out-in">
            <component :is="Component" :key="renderedRoute.fullPath" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getIconComponent } from '@/utils/iconMap'
import { notificationsApi } from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const sidebarOpen = ref(false)
const unreadCount = ref(0)
let timer = null

const menuItems = [
  { path: '/', label: '全馆仪表盘', icon: 'mdi-view-dashboard-outline' },
  { path: '/books', label: '书目大厅', icon: 'mdi-book-search-outline' },
  { path: '/shelf', label: '我的书架', icon: 'mdi-book-outline' },
  { path: '/borrows', label: '借阅中心', icon: 'mdi-book-clock-outline' },
  { path: '/reservations', label: '预约排队', icon: 'mdi-calendar-clock-outline' },
  { path: '/fines', label: '罚金中心', icon: 'mdi-cash-multiple' },
  { path: '/notifications', label: '消息通知', icon: 'mdi-bell-outline' },
  { group: '馆员工作台', role: 'librarian' },
  { path: '/circulation', label: '借还服务台', icon: 'mdi-barcode-scan', role: 'librarian' },
  { path: '/readers', label: '读者档案', icon: 'mdi-account-group', role: 'librarian' },
  { path: '/analytics', label: '统计报表', icon: 'mdi-chart-box-outline' },
  { group: '系统管理', role: 'admin' },
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
  admin: 'role-admin',
  librarian: 'role-librarian',
  reader: 'role-reader'
}[userStore.user?.role] || 'role-default'))

const userInitial = computed(() => {
  const name = userStore.user?.full_name || userStore.user?.username || '?'
  return name.charAt(0).toUpperCase()
})

function isActive(path) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}

async function loadUnreadCount() {
  try {
    const { data } = await notificationsApi.getList({ unread_only: true, limit: 200 })
    unreadCount.value = data.length
  } catch (err) {
    // 顶栏角标失败不打断主流程
  }
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadUnreadCount()
  timer = setInterval(loadUnreadCount, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

// 进入通知页后重新拉取，保证已读状态及时同步到角标
watch(() => route.path, (path) => {
  if (path === '/notifications') loadUnreadCount()
})
</script>
