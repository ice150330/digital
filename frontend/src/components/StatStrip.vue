<script setup lang="ts">
import Icon from './Icon.vue'

defineProps<{
  items: Array<{ label: string; value: string; hint?: string; icon?: string; tone?: 'primary' | 'success' | 'warning' | 'danger' | 'info' }>
}>()
</script>

<template>
  <div class="stat-strip">
    <div v-for="item in items" :key="item.label" class="stat-item">
      <div class="stat-top">
        <Icon v-if="item.icon" :icon="item.icon" size="sm" class="stat-icon" :class="`tone-${item.tone || 'primary'}`" />
        <span class="stat-label">{{ item.label }}</span>
      </div>
      <strong class="stat-value tabular-nums">{{ item.value }}</strong>
      <span v-if="item.hint" class="stat-hint">{{ item.hint }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-3); }
.stat-item { min-width: 0; padding: var(--space-4); background: var(--bg-card); border: 1px solid var(--border-default); border-radius: var(--radius-lg); box-shadow: var(--shadow-xs); }
.stat-top { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-2); }
.stat-label, .stat-hint { color: var(--text-secondary); font-size: var(--font-size-xs); }
.stat-value { display: block; color: var(--text-title); font-family: var(--font-family-number); font-size: var(--font-size-xl); }
.stat-hint { display: block; margin-top: var(--space-1); }
.tone-primary { color: var(--color-primary-600); }
.tone-success { color: var(--color-success); }
.tone-warning { color: var(--color-warning); }
.tone-danger { color: var(--color-danger); }
.tone-info { color: var(--color-info); }
</style>
