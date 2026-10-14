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
  const base = 'neo-card'

  const paddings = {
    none: '',
    small: 'p-4',
    normal: 'p-5',
    large: 'p-6'
  }

  const interactive = props.hover || props.clickable
    ? 'neo-card-hover'
    : ''

  const cursor = props.clickable ? 'cursor-pointer' : ''

  return [base, paddings[props.padding], interactive, cursor].filter(Boolean).join(' ')
})
</script>
