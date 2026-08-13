<script setup lang="ts">
import Icon from './Icon.vue'
import type { ToolTraceItem } from '../api/agent'
import ToolStep from './ToolStep.vue'

defineProps<{ trace: ToolTraceItem[]; streaming?: boolean }>()
const emit = defineEmits<{ retry: [item: ToolTraceItem] }>()
</script>

<template>
  <section class="tool-timeline">
    <header>
      <div class="timeline-title"><Icon icon="uil:process" size="sm" /><strong>工具执行</strong></div>
      <span>{{ trace.length }} 步</span>
    </header>
    <div v-if="!trace.length" class="timeline-empty">本轮没有调用分析工具。</div>
    <div v-else class="timeline-items">
      <ToolStep v-for="(item, index) in trace" :key="`${item.tool}-${index}`" :item="item" @retry="emit('retry', $event)" />
    </div>
    <div v-if="streaming" class="timeline-live"><span class="live-dot" /> 正在整理工具结果…</div>
  </section>
</template>

<style scoped>
.tool-timeline { padding: var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-card); }
.tool-timeline header { display: flex; align-items: center; justify-content: space-between; padding-bottom: var(--space-3); border-bottom: 1px solid var(--border-default); color: var(--text-secondary); font-size: var(--font-size-xs); }
.timeline-title { display: flex; align-items: center; gap: var(--space-2); color: var(--text-title); font-size: var(--font-size-sm); }
.timeline-items { margin-top: var(--space-2); }
.timeline-empty { padding: var(--space-4) 0; color: var(--text-secondary); font-size: var(--font-size-sm); }
.timeline-live { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-3); color: var(--color-primary-600); font-size: var(--font-size-xs); }
.live-dot { width: var(--space-2); height: var(--space-2); border-radius: var(--radius-full); background: currentColor; animation: pulse 1s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: 0.35; } }
@media (prefers-reduced-motion: reduce) { .live-dot { animation: none; } }
</style>
