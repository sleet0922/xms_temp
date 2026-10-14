<template>
  <div class="flex flex-col items-center justify-center py-12 px-4 text-center">
    <component :is="icon" class="w-10 h-10 text-gray-300 mb-3" stroke-width="1.2" />
    <p class="text-sm text-gray-600">{{ title }}</p>
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
