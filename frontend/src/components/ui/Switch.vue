<template>
  <HeadlessSwitch
    v-model="enabled"
    :class="[
      enabled ? 'bg-blue-600' : 'bg-gray-200',
      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
    ]"
  >
    <span
      :class="[
        enabled ? 'translate-x-6' : 'translate-x-1',
        'inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200'
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
