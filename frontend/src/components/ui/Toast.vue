<template>
  <div v-if="toasts.length" class="fixed top-16 left-1/2 -translate-x-1/2 z-50 w-[min(24rem,calc(100vw-2rem))]" aria-live="polite" aria-atomic="false">
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
  const base = 'bg-white border border-[#e5e6eb] rounded shadow-lg px-4 py-3 text-[#1d2129]'

  const types = {
    success: '[&_svg:first-child]:text-[#00b42a]',
    error: '[&_svg:first-child]:text-[#f53f3f]',
    warning: '[&_svg:first-child]:text-[#ff7d00]',
    info: '[&_svg:first-child]:text-[#165dff]'
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
