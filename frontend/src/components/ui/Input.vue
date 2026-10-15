<template>
  <div :class="['w-full', $attrs.class]" :style="$attrs.style">
    <label v-if="label" :for="inputId" class="block text-sm text-gray-600 mb-1.5">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <div class="relative">
      <div v-if="prependIcon" class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <component :is="prependIcon" class="h-4 w-4 text-gray-400" aria-hidden="true" />
      </div>

      <input
        v-bind="inputAttrs"
        :id="inputId"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :autocomplete="autocomplete"
        :name="name"
        :class="inputClasses"
        @input="$emit('update:modelValue', $event.target.value)"
        @blur="$emit('blur', $event)"
        @focus="$emit('focus', $event)"
      />

      <button
        v-if="appendIcon"
        type="button"
        class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-700 focus:outline-none focus:text-primary-600"
        :aria-label="appendLabel"
        @click="$emit('append-click')"
      >
        <component :is="appendIcon" class="h-4 w-4" aria-hidden="true" />
      </button>
    </div>

    <p v-if="error" class="mt-1 text-xs text-[#b42318]">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-xs text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed, useAttrs } from 'vue'

// min / max / step / maxlength / 键盘事件等原生属性要落到真实 <input> 上，而不是外层容器
defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const inputAttrs = computed(() => {
  const { class: _class, style: _style, ...rest } = attrs
  return rest
})

const props = defineProps({
  modelValue: [String, Number],
  label: String,
  type: {
    type: String,
    default: 'text'
  },
  placeholder: String,
  autocomplete: String,
  name: String,
  disabled: Boolean,
  required: Boolean,
  error: String,
  hint: String,
  prependIcon: Object,
  appendIcon: Object,
  appendLabel: {
    type: String,
    default: '显示或隐藏内容'
  }
})

defineEmits(['update:modelValue', 'blur', 'focus', 'append-click'])

const inputId = computed(() => `input-${Math.random().toString(36).substr(2, 9)}`)

const inputClasses = computed(() => {
  const base = 'neo-control block w-full px-3 py-2 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed'

  const padding = {
    left: props.prependIcon ? 'pl-9' : '',
    right: props.appendIcon ? 'pr-10' : ''
  }

  const borderColor = props.error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : ''

  return [base, padding.left, padding.right, borderColor].filter(Boolean).join(' ')
})
</script>
