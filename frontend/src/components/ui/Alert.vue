<template>
  <div v-if="modelValue" :class="alertClasses" role="alert">
    <div class="flex items-start gap-3">
      <component :is="getIcon()" class="w-4 h-4 flex-shrink-0 mt-0.5" />
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
  const base = 'rounded-lg border px-4 py-3'

  const variants = {
    success: 'bg-[#e8ffea] border-[#aff0b5] text-[#252522] [&>div>svg]:text-[#00b42a]',
    error: 'bg-[#ffece8] border-[#fdcdc5] text-[#252522] [&>div>svg]:text-[#f53f3f]',
    warning: 'bg-[#fff7e8] border-[#ffe4ba] text-[#252522] [&>div>svg]:text-[#ff7d00]',
    info: 'bg-[#e8f0eb] border-[#b7cec4] text-[#252522] [&>div>svg]:text-[#2f5b4e]'
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
