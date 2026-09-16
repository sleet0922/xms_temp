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
      class="w-5 h-5 mr-2"
      aria-hidden="true"
    />

    <span v-if="!loading"><slot /></span>
    <span v-else class="flex items-center">
      <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      加载中...
    </span>

    <component
      v-if="appendIcon"
      :is="appendIcon"
      class="w-5 h-5 ml-2"
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
  const base = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]'

  const sizes = {
    small: 'px-3 py-1.5 text-sm rounded-lg',
    medium: 'px-4 py-2 text-base rounded-lg',
    large: 'px-6 py-3 text-lg rounded-xl'
  }

  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 hover:-translate-y-0.5 hover:shadow shadow-sm',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:-translate-y-0.5 hover:shadow-sm',
    danger: 'bg-red-600 text-white hover:bg-red-700 hover:-translate-y-0.5 hover:shadow shadow-sm',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100',
    outline: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:-translate-y-0.5 hover:shadow-sm'
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
