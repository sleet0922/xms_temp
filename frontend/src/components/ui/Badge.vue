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
  const base = 'neo-badge inline-flex items-center whitespace-nowrap'

  const sizes = {
    small: 'px-1.5 text-xs',
    medium: 'px-2 text-xs !leading-6'
  }

  const variants = {
    default: 'bg-[#f2f3f5] text-[#4e5969]',
    primary: 'bg-[#e8f0eb] text-[#2f5b4e]',
    secondary: 'bg-[#f2f3f5] text-[#4e5969]',
    success: 'bg-[#e8ffea] text-[#00b42a]',
    danger: 'bg-[#ffece8] text-[#f53f3f]',
    warning: 'bg-[#fff7e8] text-[#ff7d00]'
  }

  return [base, sizes[props.size], variants[props.variant]].join(' ')
})
</script>
