<script setup lang="ts">
import Icon from './Icon.vue'

defineProps<{
  label: string
  value: string
  hint?: string
  loading?: boolean
  icon?: string
  tone?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info'
}>()
</script>

<template>
  <div class="kpi" :aria-busy="loading || undefined">
    <template v-if="loading">
      <div class="skeleton skeleton-label" />
      <div class="skeleton skeleton-value" />
      <div class="skeleton skeleton-hint" />
    </template>
    <template v-else>
    <div class="kpi-head">
      <div class="label">{{ label }}</div>
      <span v-if="icon" class="kpi-icon" :class="`tone-${tone || 'primary'}`"><Icon :icon="icon" size="md" /></span>
    </div>
    <div class="value tabular-nums">{{ value }}</div>
    <div v-if="hint" class="hint">{{ hint }}</div>
    </template>
  </div>
</template>

<style scoped>
.kpi {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-card);
  padding: var(--space-3);
  box-shadow: var(--shadow-xs);
}
.label {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}
.kpi-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--space-2); }
.kpi-icon { display: grid; width: 28px; height: 28px; place-items: center; border-radius: var(--radius-sm); }
.tone-primary { background: var(--color-primary-50); color: var(--color-primary-600); }
.tone-secondary { background: var(--color-secondary-50); color: var(--color-secondary-600); }
.tone-success { background: var(--color-success-bg); color: var(--color-success-text); }
.tone-warning { background: var(--color-warning-bg); color: var(--color-warning-text); }
.tone-danger { background: var(--color-danger-bg); color: var(--color-danger-text); }
.tone-info { background: var(--color-info-bg); color: var(--color-info-text); }
.value {
  color: var(--text-title);
  font-family: var(--font-family-number);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  line-height: 1.2;
}
.hint {
  margin-top: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}
.skeleton {
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--bg-subtle), var(--color-gray-200), var(--bg-subtle));
  background-size: 200% 100%;
  animation: shimmer var(--motion-duration-slow) var(--motion-easing-default) infinite;
}
.skeleton-label { width: 42%; height: var(--space-3); }
.skeleton-value { width: 64%; height: var(--font-size-2xl); margin-top: var(--space-2); }
.skeleton-hint { width: 54%; height: var(--space-2); margin-top: var(--space-2); }
@keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@media (prefers-reduced-motion: reduce) { .skeleton { animation: none; } }
</style>
