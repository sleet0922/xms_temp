<template>
  <div v-if="modelValue" :class="alertClasses" role="alert">
    <div class="flex items-start gap-3">
      <component :is="getIcon()" class="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div class="flex-1 min-w-0">
        <p v-if="title" class="font-medium mb-1">{{ title }}</p>
        <p class="text-sm">
          <slot>{{ message }}</slot>
        </p>
      </div>
      <button
        v-if="closable"
        @click="$emit('update:modelValue', false)"
        class="text-current opacity-70 hover:opacity-100 transition-opacity flex-shrink-0"
      >
        <XMarkIcon class="w-5 h-5" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: true
  },
  variant: {
    type: String,
    default: 'info',
    validator: (v) => ['success', 'error', 'warning', 'info'].includes(v)
  },
  title: String,
  message: String,
  closable: Boolean
})

defineEmits(['update:modelValue'])

const alertClasses = computed(() => {
  const base = 'rounded-2xl border p-4 shadow-sm'

  const variants = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  }

  return [base, variants[props.variant]].join(' ')
})

const getIcon = () => {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationCircleIcon,
    info: InformationCircleIcon
  }
  return icons[props.variant]
}
</script>
