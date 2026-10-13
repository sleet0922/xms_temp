<template>
  <div v-if="toasts.length" class="fixed top-4 right-4 z-50 w-[min(24rem,calc(100vw-2rem))]" aria-live="polite" aria-atomic="false">
    <TransitionGroup
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 translate-x-8"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition-all duration-150 ease-out"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-8"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="toastClasses(toast.type)"
        class="mb-3"
        role="status"
      >
        <div class="flex items-start gap-3">
          <component :is="getIcon(toast.type)" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium">{{ toast.message }}</p>
          </div>
          <button
            type="button"
            @click="remove(toast.id)"
            aria-label="关闭提示"
            class="p-1 rounded-lg text-gray-400 hover:bg-black/5 hover:text-gray-700 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-[#2f6f68] focus:ring-offset-2 active:scale-[0.98] flex-shrink-0"
          >
            <XMarkIcon class="w-5 h-5" />
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
  const base = 'bg-white border rounded-xl shadow-lg p-4 transition-all duration-150'

  const types = {
    success: 'border-[#cfe4dd] text-[#24564f]',
    error: 'border-[#efd1d1] text-[#8d3f41]',
    warning: 'border-[#eeddbf] text-[#7d5a27]',
    info: 'border-[#d1dfeb] text-[#3f617f]'
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
