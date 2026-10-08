<template>
  <HeadlessSwitch
    v-model="enabled"
    :class="[
      enabled ? 'bg-[#3d777b] shadow-[inset_2px_2px_5px_rgba(30,70,72,.35)]' : 'bg-[#d4dde4] shadow-[inset_3px_3px_7px_rgba(159,172,187,.45),inset_-3px_-3px_7px_rgba(255,255,255,.8)]',
      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:ring-offset-2'
    ]"
  >
    <span
      :class="[
        enabled ? 'translate-x-6' : 'translate-x-1',
        'inline-block h-4 w-4 transform rounded-full bg-[#e8edf2] shadow-[2px_2px_5px_rgba(36,56,66,.3),-2px_-2px_5px_rgba(255,255,255,.8)] transition-transform duration-200'
      ]"
    />
  </HeadlessSwitch>
</template>

<script setup>
import { computed } from 'vue'
import { Switch as HeadlessSwitch } from '@headlessui/vue'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue'])

const enabled = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})
</script>
