<template>
  <div class="neo-card px-5 py-4">
    <div class="flex items-center justify-between gap-4">
      <div class="text-sm text-gray-600">{{ label }}</div>
      <component v-if="icon" :is="icon" :class="['w-5 h-5 flex-shrink-0', tone.icon]" />
    </div>
    <div class="mt-2 text-[28px] leading-9 font-semibold text-gray-900 tabular-nums">{{ value }}</div>
    <div v-if="hint" class="mt-1 text-xs text-gray-500 truncate">{{ hint }}</div>
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

// 图标只做小面积色彩提示，数字本身保持中性
const tones = {
  primary: { icon: 'text-[#165dff]' },
  success: { icon: 'text-[#00b42a]' },
  warning: { icon: 'text-[#ff7d00]' },
  danger: { icon: 'text-[#f53f3f]' },
  neutral: { icon: 'text-[#86909c]' }
}

const tone = computed(() => tones[props.tone] || tones.primary)
</script>
