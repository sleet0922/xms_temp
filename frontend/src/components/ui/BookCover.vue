<template>
  <div :class="['relative bg-gray-100 overflow-hidden flex items-center justify-center', ratioClass]">
    <img
      v-if="src && !failed"
      :src="src"
      :alt="book?.title || '图书封面'"
      class="w-full h-full object-cover"
      loading="lazy"
      @error="failed = true"
    />
    <div v-else class="flex flex-col items-center justify-center gap-1 px-2 text-center">
      <BookOpenIcon class="w-8 h-8 text-gray-300" />
      <span class="text-xs text-gray-400 line-clamp-2">{{ book?.title || '暂无封面' }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { BookOpenIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  book: { type: Object, default: () => ({}) },
  ratio: {
    type: String,
    default: '3/4',
    validator: (v) => ['3/4', '4/3', 'square', '16/9'].includes(v)
  }
})

const failed = ref(false)

// 本地抓取的封面优先（cover_file），否则回退外部链接（cover_url）
const src = computed(() => {
  if (props.book?.cover_file) return `/covers/${props.book.cover_file}`
  return props.book?.cover_url || ''
})

watch(src, () => {
  failed.value = false
})

const ratioClass = computed(() => ({
  '3/4': 'aspect-[3/4]',
  '4/3': 'aspect-[4/3]',
  square: 'aspect-square',
  '16/9': 'aspect-video'
}[props.ratio]))
</script>