<template>
  <div class="neo-card neo-card-hover px-5 py-5">
    <div class="flex items-start gap-4">
      <span v-if="icon" :class="['stat-icon', tone.bg]">
        <component :is="icon" :class="['w-5 h-5', tone.icon]" />
      </span>
      <div class="min-w-0 flex-1">
        <div class="text-sm text-gray-500">{{ label }}</div>
        <div class="mt-1 text-[26px] leading-8 font-semibold text-gray-900 tabular-nums">{{ value }}</div>
        <div v-if="hint" class="mt-1 text-xs text-gray-500 truncate">{{ hint }}</div>
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

// 彩色浅底图标块负责区分指标类型，数字本身保持中性
const tones = {
  primary: { bg: 'bg-[#e8f0eb]', icon: 'text-[#2f5b4e]' },
  success: { bg: 'bg-[#e6f8ee]', icon: 'text-[#16a34a]' },
  warning: { bg: 'bg-[#fff4e5]', icon: 'text-[#f08c00]' },
  danger: { bg: 'bg-[#ffeeee]', icon: 'text-[#f53f3f]' },
  neutral: { bg: 'bg-[#f2f3f5]', icon: 'text-[#4e5969]' }
}

const tone = computed(() => tones[props.tone] || tones.primary)
</script>
