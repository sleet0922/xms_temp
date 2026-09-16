<template>
  <div v-if="message" class="fixed top-4 right-4 z-50 max-w-sm">
    <TransitionGroup
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 translate-x-8"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-8"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="toastClasses(toast.type)"
        class="mb-3"
      >
        <div class="flex items-start gap-3">
          <component :is="getIcon(toast.type)" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium">{{ toast.message }}</p>
          </div>
          <button
            @click="remove(toast.id)"
            class="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
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

const toastClasses = (type) => {
  const base = 'bg-white border rounded-lg shadow-lg p-4 transition-all duration-200'

  const types = {
    success: 'border-green-200 text-green-800',
    error: 'border-red-200 text-red-800',
    warning: 'border-yellow-200 text-yellow-800',
    info: 'border-blue-200 text-blue-800'
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
  const id = Date.now()
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
