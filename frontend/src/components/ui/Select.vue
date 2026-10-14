<template>
  <HeadlessListbox v-model="selected" :disabled="disabled">
    <div class="relative">
      <HeadlessListboxLabel v-if="label" class="block text-sm text-gray-600 mb-1.5">
        {{ label }}
        <span v-if="required" class="text-red-500">*</span>
      </HeadlessListboxLabel>

      <HeadlessListboxButton :class="buttonClasses">
        <span v-if="!selected" class="block truncate text-gray-400">{{ placeholder }}</span>
        <span v-else class="block truncate">{{ getDisplayValue(selected) }}</span>
        <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
          <ChevronDownIcon class="h-4 w-4 text-gray-400" aria-hidden="true" />
        </span>
      </HeadlessListboxButton>
      <button
        v-if="clearable && selected"
        type="button"
        class="absolute inset-y-0 right-8 flex items-center px-1 text-gray-400 hover:text-gray-700 focus:outline-none"
        aria-label="清除选择"
        @click.stop="clearSelection"
      >
        <XMarkIcon class="h-4 w-4" aria-hidden="true" />
      </button>

      <transition
        enter-active-class="neo-select-options-motion"
        enter-from-class="opacity-0 scale-[0.98] -translate-y-1"
        enter-to-class="opacity-100 scale-100 translate-y-0"
        leave-active-class="neo-select-options-motion"
        leave-from-class="opacity-100 scale-100 translate-y-0"
        leave-to-class="opacity-0 scale-[0.98] -translate-y-1"
      >
        <HeadlessListboxOptions :class="optionsClasses" @wheel.stop>
          <HeadlessListboxOption
            v-for="option in options"
            :key="getOptionValue(option)"
            v-slot="{ active, selected: isSelected }"
            :value="option"
            as="template"
          >
            <li :class="[
              active ? 'bg-[#f2f3f5] text-gray-900' : 'text-gray-900', isSelected ? '!text-[#2f5b4e] !bg-[#e8f0eb]' : '',
              'relative cursor-pointer select-none h-9 leading-9 pl-3 pr-8 text-sm transition-colors duration-150'
            ]">
              <span :class="[isSelected ? 'font-medium' : 'font-normal', 'block truncate']">
                {{ getDisplayValue(option) }}
              </span>
              <span v-if="isSelected" class="absolute inset-y-0 right-0 flex items-center pr-3 text-[#2f5b4e]">
                <CheckIcon class="h-4 w-4" aria-hidden="true" />
              </span>
            </li>
          </HeadlessListboxOption>
        </HeadlessListboxOptions>
      </transition>

      <p v-if="error" class="mt-1 text-xs text-[#f53f3f]">{{ error }}</p>
      <p v-else-if="hint" class="mt-1 text-xs text-gray-500">{{ hint }}</p>
    </div>
  </HeadlessListbox>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  Listbox as HeadlessListbox,
  ListboxButton as HeadlessListboxButton,
  ListboxOptions as HeadlessListboxOptions,
  ListboxOption as HeadlessListboxOption,
  ListboxLabel as HeadlessListboxLabel
} from '@headlessui/vue'
import { CheckIcon, ChevronDownIcon, XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: [String, Number, Object],
  options: {
    type: Array,
    required: true
  },
  label: String,
  placeholder: {
    type: String,
    default: '请选择'
  },
  itemTitle: {
    type: String,
    default: 'label'
  },
  itemValue: {
    type: String,
    default: 'value'
  },
  disabled: Boolean,
  required: Boolean,
  error: String,
  hint: String,
  clearable: Boolean,
  returnObject: Boolean
})

const emit = defineEmits(['update:modelValue'])

const selected = computed({
  get: () => {
    if (props.modelValue === null || props.modelValue === undefined || props.modelValue === '') return null
    if (props.returnObject) return props.modelValue
    return props.options.find(option => getOptionValue(option) === props.modelValue) || null
  },
  set: (value) => emit('update:modelValue', props.returnObject ? value : getOptionValue(value))
})

const buttonClasses = computed(() => {
  const base = 'neo-select-button relative w-full cursor-pointer pl-3 pr-10 text-left text-sm focus:outline-none disabled:bg-gray-50 disabled:cursor-not-allowed'

  const borderColor = props.error
    ? 'border-red-300'
    : ''

  return [base, borderColor].join(' ')
})

const optionsClasses = 'absolute z-30 mt-1 max-h-60 w-full overflow-y-auto overscroll-contain scrollbar-thin rounded-lg bg-white py-1 border border-gray-200 focus:outline-none'

const getDisplayValue = (option) => {
  if (!option) return ''
  if (typeof option === 'object') {
    return option[props.itemTitle]
  }
  return option
}

const getOptionValue = (option) => {
  if (typeof option === 'object') {
    return option[props.itemValue]
  }
  return option
}

const clearSelection = () => emit('update:modelValue', null)
</script>
