<template>
  <div class="w-full">
    <label v-if="label" class="block text-sm font-medium text-gray-700 mb-1">
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

    <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-sm text-gray-500">{{ hint }}</p>
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
  const base = 'neo-textarea block w-full px-3 py-2 rounded-xl transition-all duration-200 focus:outline-none disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed resize-y'

  const borderColor = props.error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : ''

  return [base, borderColor].join(' ')
})
</script>
