<template>
  <HeadlessTabGroup :selected-index="selectedIndex" @change="handleChange">
    <HeadlessTabList class="flex gap-2 border-b border-gray-200">
      <HeadlessTab v-for="(tab, index) in tabs" :key="index" v-slot="{ selected }" as="template">
        <button :class="[
          'px-4 py-2 text-sm font-medium transition-all duration-200 border-b-2 -mb-px focus:outline-none',
          selected
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
        ]">
          {{ tab }}
        </button>
      </HeadlessTab>
    </HeadlessTabList>

    <HeadlessTabPanels class="mt-4">
      <HeadlessTabPanel
        v-for="(_, index) in tabs"
        :key="index"
        class="focus:outline-none"
      >
        <slot :name="`panel-${index}`" />
      </HeadlessTabPanel>
    </HeadlessTabPanels>
  </HeadlessTabGroup>
</template>

<script setup>
import { computed } from 'vue'
import {
  TabGroup as HeadlessTabGroup,
  TabList as HeadlessTabList,
  Tab as HeadlessTab,
  TabPanels as HeadlessTabPanels,
  TabPanel as HeadlessTabPanel
} from '@headlessui/vue'

const props = defineProps({
  tabs: {
    type: Array,
    required: true
  },
  modelValue: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:modelValue'])

const selectedIndex = computed(() => props.modelValue)

const handleChange = (index) => {
  emit('update:modelValue', index)
}
</script>
