<script setup lang="ts">
import Icon from './Icon.vue'
import Tag from './Tag.vue'

withDefaults(defineProps<{
  code: string
  message: string
  count?: number | null
  severity?: 'warning' | 'danger' | 'info'
}>(), { count: null, severity: 'warning' })
</script>

<template>
  <div class="quality-row">
    <span class="quality-icon" :class="`severity-${severity}`">
      <Icon :icon="severity === 'danger' ? 'uil:exclamation-octagon' : 'uil:exclamation-triangle'" size="md" />
    </span>
    <div class="quality-copy">
      <div class="quality-head"><strong>{{ code }}</strong><Tag :tone="severity">{{ severity === 'danger' ? '严重' : severity === 'info' ? '提示' : '告警' }}</Tag></div>
      <p>{{ message }}</p>
    </div>
    <span v-if="count != null" class="quality-count">{{ count.toLocaleString('zh-CN') }}</span>
  </div>
</template>

<style scoped>
.quality-row { display: flex; align-items: flex-start; gap: var(--space-3); padding: var(--space-3) 0; border-bottom: 1px solid var(--border-default); }
.quality-row:last-child { border-bottom: 0; }
.quality-icon { display: grid; width: 28px; height: 28px; flex: 0 0 auto; place-items: center; border-radius: var(--radius-sm); }
.severity-warning { background: var(--color-warning-bg); color: var(--color-warning-text); }
.severity-danger { background: var(--color-danger-bg); color: var(--color-danger-text); }
.severity-info { background: var(--color-info-bg); color: var(--color-info-text); }
.quality-copy { min-width: 0; flex: 1; }
.quality-head { display: flex; align-items: center; gap: var(--space-2); }
.quality-head strong { color: var(--text-title); font-family: var(--font-family-code); font-size: var(--font-size-xs); }
.quality-copy p { margin: var(--space-1) 0 0; color: var(--text-secondary); font-size: var(--font-size-xs); line-height: 1.6; }
.quality-count { color: var(--text-title); font-family: var(--font-family-number); font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); }
</style>
