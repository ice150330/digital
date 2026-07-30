<script setup lang="ts">
import { ElCollapse, ElCollapseItem, ElTag } from 'element-plus'
import type { ToolTraceItem } from '../api/agent'

defineProps<{
  trace: ToolTraceItem[]
}>()
</script>

<template>
  <ElCollapse>
    <ElCollapseItem title="tool_trace（工具执行轨迹）" name="trace">
      <div v-for="(t, i) in trace" :key="i" class="trace-item">
        <div>
          <ElTag :type="t.ok ? 'success' : 'danger'" size="small">{{ t.tool }}</ElTag>
          <span class="mono muted" style="margin-left: 8px">{{ JSON.stringify(t.args || {}) }}</span>
        </div>
        <pre v-if="t.error" class="err">{{ t.error }}</pre>
        <pre v-else class="json">{{ JSON.stringify(t.result, null, 2) }}</pre>
      </div>
    </ElCollapseItem>
  </ElCollapse>
</template>

<style scoped>
.trace-item {
  margin-bottom: 10px;
}
.json,
.err {
  font-family: var(--font-mono);
  font-size: 11px;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 6px;
  overflow: auto;
  max-height: 200px;
}
.err {
  color: var(--color-danger);
}
</style>
