<template>
  <div :class="cardClasses">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  padding: {
    type: String,
    default: 'normal',
    validator: (v) => ['none', 'small', 'normal', 'large'].includes(v)
  },
  hover: Boolean,
  clickable: Boolean
})

const cardClasses = computed(() => {
  const base = 'bg-white border border-gray-200 rounded-xl shadow-sm transition-all duration-200'

  const paddings = {
    none: '',
    small: 'p-4',
    normal: 'p-6',
    large: 'p-8'
  }

  const interactive = props.hover || props.clickable
    ? 'hover:-translate-y-0.5 hover:shadow-md'
    : ''

  const cursor = props.clickable ? 'cursor-pointer' : ''

  return [base, paddings[props.padding], interactive, cursor].filter(Boolean).join(' ')
})
</script>
