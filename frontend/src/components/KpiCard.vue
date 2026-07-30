<script setup lang="ts">
defineProps<{
  label: string
  value: string
  hint?: string
}>()
</script>

<template>
  <div class="kpi">
    <div class="label">{{ label }}</div>
    <div class="value tabular-nums">{{ value }}</div>
    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
.kpi {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px 18px;
}
.label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}
.value {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}
.hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
