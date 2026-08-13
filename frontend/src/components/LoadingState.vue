<script setup lang="ts">
import Icon from './Icon.vue'

withDefaults(defineProps<{ label?: string; rows?: number }>(), {
  label: '正在加载分析结果…',
  rows: 3,
})
</script>

<template>
  <div class="loading-state" role="status" aria-live="polite">
    <div class="loading-title"><Icon icon="uil:spinner-alt" size="md" /><span>{{ label }}</span></div>
    <div class="loading-lines" aria-hidden="true">
      <span v-for="index in rows" :key="index" :class="`line-${index}`" />
    </div>
  </div>
</template>

<style scoped>
.loading-state { padding: var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--bg-card); }
.loading-title { display: flex; align-items: center; gap: var(--space-2); color: var(--text-secondary); font-size: var(--font-size-sm); }
.loading-title :deep(.app-icon) { color: var(--color-primary-500); animation: spin var(--motion-duration-slow) linear infinite; }
.loading-lines { display: flex; flex-direction: column; gap: var(--space-2); margin-top: var(--space-4); }
.loading-lines span { height: var(--space-3); border-radius: var(--radius-sm); background: linear-gradient(90deg, var(--bg-subtle), var(--color-gray-200), var(--bg-subtle)); background-size: 200% 100%; animation: shimmer var(--motion-duration-slow) var(--motion-easing-default) infinite; }
.line-2 { width: 82%; }
.line-3 { width: 64%; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@media (prefers-reduced-motion: reduce) { .loading-title :deep(.app-icon), .loading-lines span { animation: none; } }
</style>
