<template>
  <div class="admin-shell min-h-[100dvh]">
    <div
      v-if="sidebarOpen"
      class="admin-backdrop fixed inset-0 z-30 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <aside
      :class="[
        'admin-sidebar fixed inset-y-0 left-0 z-40 w-[244px] transform lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
    >
      <div class="flex h-full flex-col">
        <nav class="flex-1 overflow-y-auto scrollbar-thin pb-4" aria-label="后台导航">
          <template v-for="group in visibleGroups" :key="group.title">
            <div class="admin-nav-group">{{ group.title }}</div>
            <RouterLink
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="admin-nav-item"
              :class="{ 'is-active': isActive(item.path) }"
              @click="sidebarOpen = false"
            >
              <component :is="getIconComponent(item.icon)" class="h-4 w-4 shrink-0" />
              <span class="truncate">{{ item.label }}</span>
            </RouterLink>
          </template>
        </nav>
      </div>
    </aside>

    <div class="min-h-[100dvh] lg:pl-[244px]">
      <header class="admin-header sticky top-0 z-20 flex items-center gap-3 px-4 sm:px-5">
        <button
          type="button"
          aria-label="打开后台导航"
          class="admin-header-btn lg:hidden"
          @click="sidebarOpen = true"
        >
          <component :is="getIconComponent('mdi-menu')" class="h-5 w-5" />
        </button>
        <div class="admin-breadcrumb min-w-0">
          <span class="hidden sm:inline">管理后台</span>
          <span class="hidden sm:inline text-gray-300">/</span>
          <strong class="truncate">{{ route.meta.title || '概览' }}</strong>
        </div>
        <div class="ml-auto flex items-center gap-1">
          <RouterLink to="/" class="admin-header-btn">
            <component :is="getIconComponent('mdi-home-variant-outline')" class="h-4 w-4" />
            <span class="hidden sm:inline">读者端</span>
          </RouterLink>
          <span class="mx-1.5 hidden h-5 w-px bg-gray-200 sm:block" aria-hidden="true"></span>
          <RouterLink to="/profile" class="admin-header-btn" :title="`${displayName}（${roleLabel}）`">
            <component :is="getIconComponent('mdi-account-outline')" class="h-4 w-4 sm:hidden" />
            <span class="hidden max-w-32 truncate sm:inline">{{ displayName }}</span>
            <span class="admin-user-role hidden md:inline-block">{{ roleLabel }}</span>
          </RouterLink>
          <button type="button" class="admin-header-btn" title="退出登录" aria-label="退出登录" @click="handleLogout">
            <component :is="getIconComponent('mdi-logout')" class="h-4 w-4" />
          </button>
        </div>
      </header>

      <main>
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
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getIconComponent } from '@/utils/iconMap'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const sidebarOpen = ref(false)

const menuGroups = [
  { title: '工作台', items: [
    { path: '/admin', label: '概览', icon: 'mdi-view-dashboard-outline' },
    { path: '/admin/circulation', label: '借还工作台', icon: 'mdi-barcode-scan' }
  ] },
  { title: '资源管理', items: [
    { path: '/admin/books', label: '馆藏与书目', icon: 'mdi-bookshelf' },
    { path: '/admin/readers', label: '用户管理', icon: 'mdi-account-group-outline' }
  ] },
  { title: '业务记录', items: [
    { path: '/admin/borrows', label: '借阅记录', icon: 'mdi-book-clock-outline' },
    { path: '/admin/reservations', label: '预约管理', icon: 'mdi-calendar-clock-outline' },
    { path: '/admin/fines', label: '罚金处理', icon: 'mdi-cash-multiple' },
    { path: '/admin/analytics', label: '统计报表', icon: 'mdi-chart-box-outline' }
  ] },
  { title: '系统', items: [
    { path: '/admin/settings', label: '系统设置', icon: 'mdi-cog-outline', role: 'admin' }
  ] }
]

const visibleGroups = computed(() => menuGroups
  .map(group => ({ ...group, items: group.items.filter(item => item.role !== 'admin' || userStore.isAdmin) }))
  .filter(group => group.items.length))
const displayName = computed(() => userStore.user?.full_name || userStore.user?.username || '')
const roleLabel = computed(() => ({ admin: '管理员', librarian: '馆员' }[userStore.user?.role] || '后台用户'))
function isActive(path) {
  return path === '/admin' ? route.path === '/admin' : route.path.startsWith(path)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>
