<template>
  <div class="flex items-center gap-1">
    <button
      v-for="star in 5"
      :key="star"
      type="button"
      :disabled="!editable"
      class="rounded-lg transition-all duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
      :class="editable ? 'hover:scale-110 active:scale-[0.98] cursor-pointer' : 'cursor-default'"
      @click="select(star)"
      @mouseenter="hovered = star"
      @mouseleave="hovered = 0"
    >
      <StarIcon
        :class="[
          starClass,
          (hovered || modelValue) >= star ? 'text-amber-500' : 'text-gray-300'
        ]"
      />
    </button>
    <span v-if="showValue" class="text-sm text-gray-500 ml-1">
      {{ Number(modelValue || 0).toFixed(1) }}
      <span v-if="count">（{{ count }} 人评分）</span>
    </span>
    <span v-else-if="count" class="text-xs text-gray-500 ml-1">{{ count }} 人评分</span>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { StarIcon } from '@heroicons/vue/24/solid'

const props = defineProps({
  modelValue: { type: [Number, String], default: 0 },
  count: { type: Number, default: 0 },
  editable: Boolean,
  size: {
    type: String,
    default: 'medium',
    validator: (v) => ['small', 'medium', 'large'].includes(v)
  },
  showValue: Boolean
})

const emit = defineEmits(['update:modelValue'])

const hovered = ref(0)

const starClass = computed(() => ({
  small: 'w-4 h-4',
  medium: 'w-5 h-5',
  large: 'w-7 h-7'
}[props.size]))

function select(star) {
  if (!props.editable) return
  emit('update:modelValue', star)
}
</script>
