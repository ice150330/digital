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
.stat-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(160px, 100%), 1fr)); gap: var(--space-3); min-width: 0; }
.stat-item { min-width: 0; padding: var(--space-4); background: var(--bg-card); border: 1px solid var(--border-default); border-radius: var(--radius-lg); box-shadow: var(--shadow-xs); }
.stat-top { display: flex; align-items: center; gap: var(--space-2); min-width: 0; margin-bottom: var(--space-2); }
.stat-label, .stat-hint { min-width: 0; color: var(--text-secondary); font-size: var(--font-size-xs); overflow-wrap: anywhere; }
.stat-value { display: block; min-width: 0; overflow: hidden; color: var(--text-title); font-family: var(--font-family-number); font-size: var(--font-size-xl); text-overflow: ellipsis; white-space: nowrap; }
.stat-hint { display: block; margin-top: var(--space-1); }
.tone-primary { color: var(--color-primary-600); }
.tone-success { color: var(--color-success); }
.tone-warning { color: var(--color-warning); }
.tone-danger { color: var(--color-danger); }
.tone-info { color: var(--color-info); }
@media (max-width: 520px) {
  .stat-strip { grid-template-columns: 1fr; }
  .stat-item { padding: var(--space-3); }
}
</style>
