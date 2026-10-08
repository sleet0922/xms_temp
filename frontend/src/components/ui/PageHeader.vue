<template>
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
    <div class="min-w-0">
      <div class="flex items-center gap-3">
        <h1 class="neo-page-title text-2xl font-semibold tracking-tight truncate">{{ title }}</h1>
        <slot name="badge" />
      </div>
      <p v-if="subtitle" class="neo-page-subtitle text-sm mt-1">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="flex items-center gap-3 flex-shrink-0">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: String
})
</script>
