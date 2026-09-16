<template>
  <div class="flex items-center justify-between gap-4 flex-wrap">
    <div class="text-sm text-gray-500">
      共 {{ total }} 条 · 第 {{ page }}/{{ totalPages }} 页
    </div>

    <div class="flex items-center gap-2">
      <Button size="small" variant="outline" :disabled="page <= 1" @click="go(page - 1)">上一页</Button>

      <button
        v-for="(p, index) in pageNumbers"
        :key="index"
        :disabled="p === '...'"
        @click="p !== '...' && go(p)"
        :class="[
          'min-w-[2.25rem] h-9 px-2 rounded-lg text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          p === page
            ? 'bg-blue-600 text-white shadow-sm'
            : p === '...'
              ? 'text-gray-400 cursor-default'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:-translate-y-0.5 hover:shadow-sm active:scale-[0.98] active:translate-y-0'
        ]"
      >
        {{ p }}
      </button>

      <Button size="small" variant="outline" :disabled="page >= totalPages" @click="go(page + 1)">下一页</Button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Button from './Button.vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 24 },
  total: { type: Number, default: 0 }
})

const emit = defineEmits(['update:page'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

// 页数较多时只保留首尾与当前页附近的窗口，避免页码条溢出
const pageNumbers = computed(() => {
  const last = totalPages.value
  const current = props.page
  if (last <= 7) {
    return Array.from({ length: last }, (_, i) => i + 1)
  }
  const pages = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(last - 1, current + 1)
  if (start > 2) pages.push('...')
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < last - 1) pages.push('...')
  pages.push(last)
  return pages
})

function go(target) {
  if (target < 1 || target > totalPages.value || target === props.page) return
  emit('update:page', target)
}
</script>