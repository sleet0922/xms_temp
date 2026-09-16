<template>
  <div class="w-full">
    <label v-if="label" :for="inputId" class="block text-sm font-medium text-gray-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <div class="relative">
      <div v-if="prependIcon" class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <component :is="prependIcon" class="h-5 w-5 text-gray-400" aria-hidden="true" />
      </div>

      <input
        :id="inputId"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :class="inputClasses"
        @input="$emit('update:modelValue', $event.target.value)"
        @blur="$emit('blur', $event)"
        @focus="$emit('focus', $event)"
      />

      <div v-if="appendIcon" class="absolute inset-y-0 right-0 pr-3 flex items-center">
        <component
          :is="appendIcon"
          class="h-5 w-5 text-gray-400 cursor-pointer hover:text-gray-600"
          @click="$emit('append-click')"
          aria-hidden="true"
        />
      </div>
    </div>

    <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-sm text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: [String, Number],
  label: String,
  type: {
    type: String,
    default: 'text'
  },
  placeholder: String,
  disabled: Boolean,
  required: Boolean,
  error: String,
  hint: String,
  prependIcon: Object,
  appendIcon: Object
})

defineEmits(['update:modelValue', 'blur', 'focus', 'append-click'])

const inputId = computed(() => `input-${Math.random().toString(36).substr(2, 9)}`)

const inputClasses = computed(() => {
  const base = 'block w-full px-3 py-2 border rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed'

  const padding = {
    left: props.prependIcon ? 'pl-10' : '',
    right: props.appendIcon ? 'pr-10' : ''
  }

  const borderColor = props.error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : 'border-gray-300 focus:border-blue-500'

  return [base, padding.left, padding.right, borderColor].filter(Boolean).join(' ')
})
</script>
