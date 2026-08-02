<script setup lang="ts">
import type { ToolTraceItem } from '../api/agent'
import ToolTimeline from './ToolTimeline.vue'

defineProps<{ trace: ToolTraceItem[]; streaming?: boolean }>()
const emit = defineEmits<{ retry: [item: ToolTraceItem] }>()
</script>

<template>
  <div class="trace-panel">
    <ToolTimeline :trace="trace" :streaming="streaming" @retry="emit('retry', $event)" />
    <details v-if="trace.length" class="raw-details">
      <summary>查看原始 tool_trace</summary>
      <pre>{{ JSON.stringify(trace, null, 2) }}</pre>
    </details>
  </div>
</template>

<style scoped>
.raw-details { margin-top: var(--space-2); color: var(--text-secondary); font-size: var(--font-size-xs); }
.raw-details summary { cursor: pointer; }
.raw-details pre { max-height: 240px; overflow: auto; margin: var(--space-2) 0 0; padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-code-dark-bg); color: var(--color-code-dark-text); font-family: var(--font-family-code); font-size: var(--font-size-xs); }
</style>
