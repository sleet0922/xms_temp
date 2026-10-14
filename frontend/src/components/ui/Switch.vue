<template>
  <HeadlessSwitch
    v-model="enabled"
    :aria-label="label"
    :class="[
      enabled ? 'bg-[#165dff]' : 'bg-[#c9cdd4]',
      'relative inline-flex h-5 w-10 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-200'
    ]"
  >
    <span
      :class="[
        enabled ? 'translate-x-[22px]' : 'translate-x-1',
        'inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform duration-200'
      ]"
    />
  </HeadlessSwitch>
</template>

<script setup>
import { computed } from 'vue'
import { Switch as HeadlessSwitch } from '@headlessui/vue'

const props = defineProps({
  modelValue: Boolean,
  label: {
    type: String,
    default: '切换开关'
  }
})

const emit = defineEmits(['update:modelValue'])

const enabled = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})
</script>
