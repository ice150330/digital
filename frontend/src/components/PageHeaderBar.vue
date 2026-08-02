<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="page-header">
    <div class="page-header-copy">
      <h1>{{ title }}</h1>
      <p v-if="description" class="desc">{{ description }}</p>
    </div>
    <div class="actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.page-header-copy,
.actions {
  min-width: 0;
  max-width: 100%;
}
.actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}
</style>
