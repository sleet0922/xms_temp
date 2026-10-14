<template>
  <div :class="['book-cover relative overflow-hidden rounded-md', ratioClass]">
    <!-- 生成封面始终垫底：外链封面加载慢或失败时也不会出现空白 -->
    <div class="book-cover-fallback absolute inset-0 flex flex-col" :style="fallbackStyle" aria-hidden="true">
      <span class="book-cover-spine"></span>
      <div class="relative flex-1 flex flex-col justify-between px-[14%] pt-[24%] pb-[12%]">
        <span class="book-cover-title line-clamp-4">{{ book?.title || '暂无封面' }}</span>
        <span v-if="book?.author" class="book-cover-author line-clamp-1">{{ book.author }}</span>
      </div>
    </div>
    <img
      v-if="src && !failed"
      :src="src"
      :alt="book?.title || '图书封面'"
      class="relative w-full h-full object-cover transition-opacity duration-300"
      :class="loaded ? 'opacity-100' : 'opacity-0'"
      loading="lazy"
      @load="loaded = true"
      @error="failed = true"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  book: { type: Object, default: () => ({}) },
  ratio: {
    type: String,
    default: '3/4',
    validator: (v) => ['3/4', '4/3', 'square', '16/9'].includes(v)
  }
})

const failed = ref(false)
const loaded = ref(false)

// 本地抓取的封面优先（cover_file），否则回退外部链接（cover_url）
const src = computed(() => {
  if (props.book?.cover_file) return `/covers/${props.book.cover_file}`
  return props.book?.cover_url || ''
})

watch(src, () => {
  failed.value = false
  loaded.value = false
})

// 低饱和的书封配色，书名相同时颜色稳定
const palettes = [
  ['#2f4b7c', '#4a6fa5'],
  ['#1f5f6b', '#3a8a96'],
  ['#3c6e47', '#5e9468'],
  ['#8a4b2f', '#b0714d'],
  ['#5b4a7a', '#7d6aa0'],
  ['#273449', '#46566f'],
  ['#7a3b4c', '#a35d6f'],
  ['#3d5a80', '#5f7fa6'],
  ['#6b5a3e', '#93805f'],
  ['#2e5e5a', '#4f8783']
]

const fallbackStyle = computed(() => {
  const title = props.book?.title || ''
  let hash = 0
  for (const ch of title) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  const [from] = palettes[hash % palettes.length]
  return { background: from }
})

const ratioClass = computed(() => ({
  '3/4': 'aspect-[3/4]',
  '4/3': 'aspect-[4/3]',
  square: 'aspect-square',
  '16/9': 'aspect-video'
}[props.ratio]))
</script>
