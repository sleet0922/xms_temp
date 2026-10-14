<template>
  <div class="min-h-[100dvh] flex flex-col">
    <header class="site-header">
      <div class="site-header-inner">
        <nav class="site-nav hidden lg:flex" aria-label="主导航">
          <RouterLink
            v-for="item in primaryMenu"
            :key="item.path"
            :to="item.path"
            class="site-nav-item"
            :class="{ 'is-active': isActive(item.path) }"
          >
            {{ item.label }}
          </RouterLink>
        </nav>

        <div class="ml-auto flex items-center gap-2">
          <RouterLink to="/notifications" aria-label="消息通知" title="消息通知" class="site-icon-btn">
            <component :is="getIconComponent('mdi-bell-outline')" class="w-5 h-5" />
            <span v-if="unreadCount > 0" class="site-dot">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </RouterLink>

          <div ref="menuRef" class="relative">
            <button
              type="button"
              class="flex items-center gap-2 h-8 pl-1 pr-2 rounded hover:bg-gray-100 transition-colors"
              :aria-expanded="userMenuOpen"
              aria-haspopup="menu"
              @click="userMenuOpen = !userMenuOpen"
            >
              <span class="hidden sm:block text-sm text-gray-900 max-w-[8rem] truncate">{{ displayName }}</span>
              <component :is="getIconComponent('mdi-chevron-down')" class="hidden sm:block w-3.5 h-3.5 text-gray-500" />
            </button>
            <div v-if="userMenuOpen" class="site-user-menu" role="menu">
              <div class="px-3 py-2 border-b border-gray-200 mb-1">
                <div class="text-sm text-gray-900 truncate">{{ displayName }}</div>
                <div class="text-xs text-gray-500">{{ roleLabel }}</div>
              </div>
              <RouterLink to="/profile" role="menuitem" @click="userMenuOpen = false">
                <component :is="getIconComponent('mdi-account-outline')" class="w-4 h-4 text-gray-500" />个人中心
              </RouterLink>
              <RouterLink v-if="userStore.isLibrarian" to="/admin" role="menuitem" @click="userMenuOpen = false">
                <component :is="getIconComponent('mdi-shield-crown-outline')" class="w-4 h-4 text-gray-500" />管理后台
              </RouterLink>
              <button type="button" role="menuitem" class="border-t border-gray-200 mt-1" @click="handleLogout">
                <component :is="getIconComponent('mdi-logout')" class="w-4 h-4 text-gray-500" />退出登录
              </button>
            </div>
          </div>

          <button
            type="button"
            aria-label="打开导航菜单"
            class="site-icon-btn lg:hidden"
            @click="mobileOpen = !mobileOpen"
          >
            <component :is="getIconComponent(mobileOpen ? 'mdi-close' : 'mdi-menu')" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>

    <Transition name="mobile-nav">
      <nav v-if="mobileOpen" class="site-mobile-nav lg:hidden" aria-label="移动端导航">
        <RouterLink
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="{ 'is-active': isActive(item.path) }"
          @click="mobileOpen = false"
        >
          <component :is="getIconComponent(item.icon)" class="w-4 h-4" />
          {{ item.label }}
        </RouterLink>
      </nav>
    </Transition>

    <main class="flex-1">
      <RouterView v-slot="{ Component, route: renderedRoute }">
        <Transition name="page-transition" mode="out-in">
          <component :is="Component" :key="renderedRoute.fullPath" />
        </Transition>
      </RouterView>
    </main>

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
const mobileOpen = ref(false)
const userMenuOpen = ref(false)
const menuRef = ref(null)
const unreadCount = ref(0)
let timer = null

const menuItems = [
  { path: '/', label: '首页', icon: 'mdi-home-variant-outline' },
  { path: '/books', label: '馆藏检索', icon: 'mdi-book-search-outline' },
  { path: '/shelf', label: '我的书架', icon: 'mdi-book-outline' },
  { path: '/borrows', label: '借阅记录', icon: 'mdi-book-clock-outline' },
  { path: '/reservations', label: '我的预约', icon: 'mdi-calendar-clock-outline' },
  { path: '/fines', label: '罚金', icon: 'mdi-cash-multiple' },
  { path: '/notifications', label: '消息通知', icon: 'mdi-bell-outline' },
  { path: '/profile', label: '个人中心', icon: 'mdi-account-outline' }
]

// 通知与个人中心放在顶栏右侧，主导航只保留业务入口
const primaryMenu = menuItems.filter(item => !['/notifications', '/profile'].includes(item.path))
const displayName = computed(() => userStore.user?.full_name || userStore.user?.username)

function handleOutsideClick(event) {
  if (menuRef.value && !menuRef.value.contains(event.target)) userMenuOpen.value = false
}

const roleLabel = computed(() => ({
  admin: '管理员',
  librarian: '馆员',
  reader: '读者'
}[userStore.user?.role] || '用户'))

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
  userMenuOpen.value = false
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  loadUnreadCount()
  timer = setInterval(loadUnreadCount, 60000)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  if (timer) clearInterval(timer)
})

// 进入通知页后重新拉取，保证已读状态及时同步到角标
watch(() => route.path, (path) => {
  mobileOpen.value = false
  userMenuOpen.value = false
  if (path === '/notifications') loadUnreadCount()
})
</script>
