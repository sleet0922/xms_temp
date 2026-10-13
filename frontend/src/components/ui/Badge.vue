<template>
  <span :class="badgeClasses">
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'primary', 'secondary', 'success', 'danger', 'warning'].includes(v)
  },
  size: {
    type: String,
    default: 'medium',
    validator: (v) => ['small', 'medium'].includes(v)
  }
})

const badgeClasses = computed(() => {
  const base = 'neo-badge inline-flex items-center font-medium rounded-lg'

  const sizes = {
    small: 'px-2 py-0.5 text-xs',
    medium: 'px-2.5 py-1 text-sm'
  }

  const variants = {
    default: 'bg-gray-100 text-gray-700',
    primary: 'bg-blue-50 text-blue-700',
    secondary: 'bg-gray-100 text-gray-700',
    success: 'bg-green-50 text-green-700',
    danger: 'bg-red-50 text-red-700',
    warning: 'bg-yellow-50 text-yellow-700'
  }

  return [base, sizes[props.size], variants[props.variant]].join(' ')
})
</script>
