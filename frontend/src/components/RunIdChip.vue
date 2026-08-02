<script setup lang="ts">
import Icon from './Icon.vue'

defineProps<{ value: string }>()
</script>

<template>
  <span class="run-chip" :title="value"><Icon icon="uil:code-branch" size="sm" /><span>{{ value }}</span></span>
</template>

<style scoped>
.run-chip { display: inline-flex; max-width: 100%; min-width: 0; min-height: var(--space-6); align-items: center; gap: var(--space-1); padding: 0 var(--space-2); overflow: hidden; border: 1px solid var(--border-default); border-radius: var(--radius-full); background: var(--bg-subtle); color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
.run-chip span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
