<template>
  <div class="neo-card neo-card-hover group p-6 transition-all duration-200">
    <div class="flex items-start justify-between gap-4">
      <div class="min-w-0">
        <div class="text-sm text-gray-500">{{ label }}</div>
        <div class="text-2xl font-semibold tracking-tight text-gray-900 mt-1">{{ value }}</div>
        <div v-if="hint" class="text-xs text-gray-500 mt-1 truncate">{{ hint }}</div>
      </div>
      <div
        v-if="icon"
        :class="['neo-stat-icon w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all duration-200 ease-out group-hover:scale-110', tone.bg, tone.hover]"
      >
        <component :is="icon" :class="['w-6 h-6 transition-colors duration-200', tone.icon, 'group-hover:text-white']" />
      </div>
    </div>
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: [String, Number],
  hint: String,
  icon: Object,
  tone: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'success', 'warning', 'danger', 'neutral'].includes(v)
  }
})

const tones = {
  primary: { bg: 'bg-blue-50', icon: 'text-blue-600', hover: 'group-hover:bg-blue-500' },
  success: { bg: 'bg-green-50', icon: 'text-green-600', hover: 'group-hover:bg-green-500' },
  warning: { bg: 'bg-amber-50', icon: 'text-amber-600', hover: 'group-hover:bg-amber-500' },
  danger: { bg: 'bg-red-50', icon: 'text-red-600', hover: 'group-hover:bg-red-500' },
  neutral: { bg: 'bg-gray-100', icon: 'text-gray-600', hover: 'group-hover:bg-gray-500' }
}

const tone = computed(() => tones[props.tone] || tones.primary)
</script>
