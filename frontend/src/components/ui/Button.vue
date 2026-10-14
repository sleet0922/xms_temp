<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    @click="handleClick"
  >
    <component
      v-if="prependIcon"
      :is="prependIcon"
      class="w-4 h-4 mr-1.5"
      aria-hidden="true"
    />

    <span v-if="!loading"><slot /></span>
    <span v-else class="flex items-center">
      <svg class="animate-spin h-4 w-4 mr-1.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      加载中...
    </span>

    <component
      v-if="appendIcon"
      :is="appendIcon"
      class="w-4 h-4 ml-1.5"
      aria-hidden="true"
    />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'danger', 'ghost', 'outline'].includes(v)
  },
  size: {
    type: String,
    default: 'medium',
    validator: (v) => ['small', 'medium', 'large'].includes(v)
  },
  block: Boolean,
  disabled: Boolean,
  loading: Boolean,
  type: {
    type: String,
    default: 'button'
  },
  prependIcon: Object,
  appendIcon: Object
})

const emit = defineEmits(['click'])

const buttonClasses = computed(() => {
  const base = 'neo-button inline-flex items-center justify-center font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-200 disabled:cursor-not-allowed whitespace-nowrap'

  const sizes = {
    small: 'px-3 text-sm !h-7',
    medium: 'px-4 text-sm',
    large: 'px-5 text-sm !h-9'
  }

  const variants = {
    primary: 'neo-button-primary',
    secondary: 'neo-button-secondary',
    danger: 'neo-button-danger',
    ghost: 'neo-button-ghost',
    outline: 'neo-button-outline'
  }

  const width = props.block ? 'w-full' : ''

  return [base, sizes[props.size], variants[props.variant], width].filter(Boolean).join(' ')
})

const handleClick = (event) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>
