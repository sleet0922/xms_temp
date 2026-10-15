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
    success: 'bg-[#e8ffea] text-[#1e6b34]',
    danger: 'bg-[#ffece8] text-[#b42318]',
    warning: 'bg-[#fff7e8] text-[#8a4b00]'
  }

  return [base, sizes[props.size], variants[props.variant]].join(' ')
})
</script>
