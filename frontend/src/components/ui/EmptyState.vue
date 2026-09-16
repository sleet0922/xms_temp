<template>
  <div class="flex flex-col items-center justify-center py-12 px-4 text-center">
    <div class="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
      <component :is="icon" class="w-6 h-6 text-gray-400" />
    </div>
    <p class="text-sm font-medium text-gray-900">{{ title }}</p>
    <p v-if="description" class="text-xs text-gray-500 mt-1 max-w-sm">{{ description }}</p>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
import { InboxIcon } from '@heroicons/vue/24/outline'

defineProps({
  title: { type: String, default: '暂无数据' },
  description: String,
  icon: { type: Object, default: () => InboxIcon }
})
</script>