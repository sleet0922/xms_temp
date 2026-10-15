<template>
  <!--
    挂到 body 下、独立于 #app：弹窗打开时 Headless UI 会把 #app 设为 inert 并盖上遮罩，
    留在 #app 内的提示会被压暗且无法点击关闭
  -->
  <Teleport to="body">
  <div v-if="toasts.length" class="neo-toast-layer fixed top-16 left-1/2 -translate-x-1/2 w-[min(24rem,calc(100vw-2rem))]" aria-live="polite" aria-atomic="false">
    <TransitionGroup
      enter-active-class="neo-toast-enter"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="neo-toast-leave"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
      move-class="neo-toast-move"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="toastClasses(toast.type)"
        class="mb-3"
        role="status"
      >
        <div class="flex items-start gap-3">
          <component :is="getIcon(toast.type)" class="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div class="flex-1 min-w-0">
            <p class="text-sm">{{ toast.message }}</p>
          </div>
          <button
            type="button"
            @click="remove(toast.id)"
            aria-label="关闭提示"
            class="p-0.5 rounded text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors flex-shrink-0"
          >
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const toasts = ref([])
let nextId = 0

const toastClasses = (type) => {
  const base = 'neo-toast-surface bg-white border rounded px-4 py-3 text-[#252522]'

  const types = {
    success: '[&_svg:first-child]:text-[#1e6b34]',
    error: '[&_svg:first-child]:text-[#b42318]',
    warning: '[&_svg:first-child]:text-[#8a4b00]',
    info: '[&_svg:first-child]:text-[#2f5b4e]'
  }

  return [base, types[type] || types.info].join(' ')
}

const getIcon = (type) => {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationCircleIcon,
    info: InformationCircleIcon
  }
  return icons[type] || icons.info
}

const show = (message, type = 'info', duration = 3500) => {
  const id = ++nextId
  toasts.value.push({ id, message, type })

  setTimeout(() => {
    remove(id)
  }, duration)
}

const remove = (id) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

defineExpose({ show })
</script>
