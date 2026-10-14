<template>
  <div class="w-full">
    <label v-if="label" class="block text-sm text-gray-600 mb-1.5">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <textarea
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :class="textareaClasses"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur', $event)"
      @focus="$emit('focus', $event)"
    />

    <p v-if="error" class="mt-1 text-xs text-[#f53f3f]">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-xs text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: String,
  label: String,
  rows: {
    type: Number,
    default: 3
  },
  placeholder: String,
  disabled: Boolean,
  required: Boolean,
  error: String,
  hint: String
})

defineEmits(['update:modelValue', 'blur', 'focus'])

const textareaClasses = computed(() => {
  const base = 'neo-textarea block w-full px-3 py-2 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed resize-y'

  const borderColor = props.error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : ''

  return [base, borderColor].join(' ')
})
</script>
