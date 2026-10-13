<template>
  <TransitionRoot :show="modelValue" as="template">
    <HeadlessDialog @close="handleClose" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-200 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-150 ease-out"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="neo-dialog-backdrop fixed inset-0" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="duration-200 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-150 ease-out"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel :class="dialogClasses">
              <div v-if="title" class="flex items-center justify-between mb-5">
                <DialogTitle class="text-xl font-semibold tracking-tight text-gray-900">
                  {{ title }}
                </DialogTitle>
                <button
                  v-if="showClose"
                  type="button"
                  @click="handleClose"
                  aria-label="关闭对话框"
                  class="p-2 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#2f6f68] focus:ring-offset-2 transition-colors duration-150 active:scale-[0.98]"
                >
                  <XMarkIcon class="w-6 h-6" />
                </button>
              </div>

              <div :class="contentClasses">
                <slot />
              </div>

              <div v-if="$slots.footer" class="mt-6 flex justify-end gap-3">
                <slot name="footer" />
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </HeadlessDialog>
  </TransitionRoot>
</template>

<script setup>
import { computed } from 'vue'
import {
  Dialog as HeadlessDialog,
  DialogPanel,
  DialogTitle,
  TransitionRoot,
  TransitionChild
} from '@headlessui/vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: Boolean,
  title: String,
  maxWidth: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl', '2xl', '4xl'].includes(v)
  },
  persistent: Boolean,
  showClose: {
    type: Boolean,
    default: true
  },
  scrollable: Boolean
})

const emit = defineEmits(['update:modelValue', 'close'])

const dialogClasses = computed(() => {
  const maxWidths = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '4xl': 'max-w-4xl'
  }

  return [
    'neo-dialog relative rounded-xl p-6 w-full',
    maxWidths[props.maxWidth]
  ].join(' ')
})

const contentClasses = computed(() => {
  return props.scrollable ? 'overflow-y-auto max-h-[60vh]' : ''
})

const handleClose = () => {
  if (!props.persistent) {
    emit('update:modelValue', false)
    emit('close')
  }
}
</script>
