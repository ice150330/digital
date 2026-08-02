<script setup lang="ts">
import { computed } from 'vue'
import { ElTooltip } from 'element-plus'
import type { PiStatusData } from '../api/agent'
import Tag from './Tag.vue'

const props = defineProps<{ runtime: string; pi?: PiStatusData | null; fallback?: boolean }>()
const tone = computed(() => props.fallback || props.pi?.is_stub ? 'warning' : props.runtime === 'pi' ? 'success' : props.runtime === 'local' ? 'primary' : 'info')
const tip = computed(() => {
  if (!props.pi) return `当前 runtime：${props.runtime}`
  const parts = [`默认 runtime：${props.pi.default_runtime ?? '-'}`]
  if (props.pi.is_stub) parts.push('Pi 为占位 stub，对话会降级到本地工具')
  if (props.pi.fallback_reason) parts.push(`降级原因：${props.pi.fallback_reason}`)
  parts.push(`skills：${(props.pi.skills || []).length} 个`)
  return parts.join('\n')
})
</script>

<template>
  <ElTooltip :content="tip" placement="bottom" raw-content>
    <Tag :tone="tone">{{ runtime }}{{ fallback ? ' · 已降级' : '' }}</Tag>
  </ElTooltip>
</template>
