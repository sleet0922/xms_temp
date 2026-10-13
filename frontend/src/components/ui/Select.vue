<template>
  <HeadlessListbox v-model="selected" :disabled="disabled">
    <div class="relative">
      <HeadlessListboxLabel v-if="label" class="block text-sm font-medium text-gray-700 mb-1">
        {{ label }}
        <span v-if="required" class="text-red-500">*</span>
      </HeadlessListboxLabel>

      <HeadlessListboxButton :class="buttonClasses">
        <span v-if="!selected" class="block truncate text-gray-400">{{ placeholder }}</span>
        <span v-else class="block truncate">{{ getDisplayValue(selected) }}</span>
        <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
          <ChevronDownIcon class="h-5 w-5 text-gray-400" aria-hidden="true" />
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
        leave-active-class="transition duration-100 ease-out"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <HeadlessListboxOptions :class="optionsClasses">
          <HeadlessListboxOption
            v-for="option in options"
            :key="getOptionValue(option)"
            v-slot="{ active, selected: isSelected }"
            :value="option"
            as="template"
          >
            <li :class="[
              active ? 'bg-[#edf5f2] text-[#24564f]' : 'text-gray-900',
              'relative cursor-pointer select-none py-2 pl-10 pr-4 transition-colors duration-150'
            ]">
              <span :class="[isSelected ? 'font-medium' : 'font-normal', 'block truncate']">
                {{ getDisplayValue(option) }}
              </span>
              <span v-if="isSelected" class="absolute inset-y-0 left-0 flex items-center pl-3 text-[#2f6f68]">
                <CheckIcon class="h-5 w-5" aria-hidden="true" />
              </span>
            </li>
          </HeadlessListboxOption>
        </HeadlessListboxOptions>
      </transition>

      <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>
      <p v-else-if="hint" class="mt-1 text-sm text-gray-500">{{ hint }}</p>
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
  const base = 'neo-select-button relative w-full cursor-pointer rounded-xl py-2 pl-3 pr-10 text-left transition-all duration-200 focus:outline-none disabled:bg-gray-50 disabled:cursor-not-allowed'

  const borderColor = props.error
    ? 'border-red-300'
    : ''

  return [base, borderColor].join(' ')
})

const optionsClasses = 'absolute z-30 mt-2 max-h-60 w-full overflow-auto scrollbar-thin rounded-xl bg-white py-1 shadow-lg border border-gray-200 focus:outline-none'

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
