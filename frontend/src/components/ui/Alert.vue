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
        type="button"
        @click="$emit('update:modelValue', false)"
        aria-label="关闭提示"
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
  const base = 'rounded-xl border p-4 shadow-sm'

  const variants = {
    success: 'bg-[#f0f8f4] border-[#cfe4dd] text-[#24564f]',
    error: 'bg-[#fdf1f1] border-[#efd1d1] text-[#8d3f41]',
    warning: 'bg-[#fff8ec] border-[#eeddbf] text-[#7d5a27]',
    info: 'bg-[#f1f6fa] border-[#d1dfeb] text-[#3f617f]'
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
