<script setup lang="ts">
import Icon from './Icon.vue'
import Tag from './Tag.vue'
import type { ToolTraceItem } from '../api/agent'
import { toolIcon, toolLabel, toolSummary } from '../composables/useToolSummary'

defineProps<{ item: ToolTraceItem }>()
const emit = defineEmits<{ retry: [item: ToolTraceItem] }>()
</script>

<template>
  <div class="tool-step" :class="{ failed: item.ok === false, running: item.ok === undefined }">
    <div class="step-icon"><Icon :icon="item.ok === false ? 'uil:exclamation-triangle' : toolIcon(item.tool)" size="md" /></div>
    <div class="step-content">
      <div class="step-head">
        <strong>{{ toolLabel(item.tool) }}</strong>
        <Tag v-if="item.ok === false" tone="danger">失败</Tag>
        <Tag v-else-if="item.ok === true" tone="success">完成</Tag>
        <Tag v-else tone="primary">执行中</Tag>
        <span v-if="item.duration_ms != null" class="duration">{{ Math.round(item.duration_ms) }} ms</span>
      </div>
      <p>{{ toolSummary(item) }}</p>
      <button v-if="item.ok === false" type="button" class="retry-link" @click="emit('retry', item)">重试此步骤</button>
    </div>
  </div>
</template>

<style scoped>
.tool-step { display: flex; gap: var(--space-3); padding: var(--space-3) 0; border-bottom: 1px solid var(--border-default); }
.tool-step:last-child { border-bottom: 0; }
.step-icon { display: grid; width: 28px; height: 28px; flex: 0 0 auto; place-items: center; border-radius: var(--radius-sm); background: var(--color-primary-50); color: var(--color-primary-600); }
.tool-step.failed .step-icon { background: var(--color-danger-bg); color: var(--color-danger); }
.tool-step.running .step-icon { background: var(--color-warning-bg); color: var(--color-warning); }
.step-content { min-width: 0; flex: 1; }
.step-head { display: flex; align-items: center; gap: var(--space-2); }
.step-head strong { color: var(--text-title); font-size: var(--font-size-sm); }
.duration { margin-left: auto; color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
.step-content p { margin: var(--space-1) 0 0; color: var(--text-secondary); font-size: var(--font-size-xs); line-height: 1.5; }
.retry-link { margin-top: var(--space-2); padding: 0; border: 0; background: transparent; color: var(--color-primary-600); cursor: pointer; font-size: var(--font-size-xs); }
</style>
