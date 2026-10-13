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
        :class="['neo-stat-icon w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all duration-200 ease-out group-hover:scale-[1.03]', tone.bg, tone.hover]"
      >
        <component :is="icon" :class="['w-6 h-6', tone.icon]" />
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
  primary: { bg: 'bg-[#edf5f2]', icon: 'text-[#2f6f68]', hover: 'group-hover:bg-[#e2efeb]' },
  success: { bg: 'bg-[#eef6f1]', icon: 'text-[#34745c]', hover: 'group-hover:bg-[#e4f1e9]' },
  warning: { bg: 'bg-[#fbf4e8]', icon: 'text-[#a87532]', hover: 'group-hover:bg-[#f7eddc]' },
  danger: { bg: 'bg-[#fbefef]', icon: 'text-[#bd5b58]', hover: 'group-hover:bg-[#f8e6e6]' },
  neutral: { bg: 'bg-[#f1f4f5]', icon: 'text-[#687780]', hover: 'group-hover:bg-[#e9eef0]' }
}

const tone = computed(() => tones[props.tone] || tones.primary)
</script>
