<script setup lang="ts">
withDefaults(defineProps<{
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  size?: 'sm' | 'md'
  metric?: boolean
}>(), { tone: 'neutral', size: 'sm', metric: false })
</script>

<template>
  <span class="app-tag" :class="[`tone-${tone}`, `size-${size}`, { 'is-metric': metric }]"><slot /></span>
</template>

<style scoped>
.app-tag { display: inline-flex; max-width: 100%; align-items: center; overflow: hidden; border: 1px solid transparent; border-radius: var(--radius-full); font-weight: var(--font-weight-medium); text-overflow: ellipsis; white-space: nowrap; }
.size-sm { min-height: var(--tag-height-sm); padding: 0 var(--space-2); font-size: var(--font-size-xs); }
.size-md { min-height: var(--tag-height-md); padding: 0 var(--space-3); font-size: var(--font-size-sm); }
.tone-primary { background: var(--color-primary-50); border-color: var(--color-primary-100); color: var(--color-primary-700); }
.tone-success { background: var(--color-success-bg); border-color: var(--color-success-border); color: var(--color-success-text); }
.tone-warning { background: var(--color-warning-bg); border-color: var(--color-warning-border); color: var(--color-warning-text); }
.tone-danger { background: var(--color-danger-bg); border-color: var(--color-danger-border); color: var(--color-danger-text); }
.tone-info { background: var(--color-info-bg); border-color: var(--color-info-border); color: var(--color-info-text); }
.tone-neutral { background: var(--bg-subtle); border-color: var(--border-default); color: var(--text-secondary); }
.is-metric { font-family: var(--font-family-number); font-variant-numeric: tabular-nums; }
</style>
