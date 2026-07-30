<script setup lang="ts">
import { computed } from 'vue'
import { ElTag, ElTooltip } from 'element-plus'
import type { PiStatusData } from '../api/agent'

const props = defineProps<{
  runtime: string
  pi?: PiStatusData | null
  fallback?: boolean
}>()

const tagType = computed(() => {
  if (props.runtime === 'pi') return 'success'
  if (props.runtime === 'local') return 'primary'
  return 'info'
})

const tip = computed(() => {
  if (!props.pi) return `runtime: ${props.runtime}`
  const parts = [`默认 runtime: ${props.pi.default_runtime ?? '-'}`]
  if (props.pi.is_stub) parts.push('Pi 为占位 stub，对话降级 local/template')
  if (props.pi.fallback_reason) parts.push(`降级原因: ${props.pi.fallback_reason}`)
  parts.push(`skills: ${(props.pi.skills || []).length} 个`)
  return parts.join('\n')
})
</script>

<template>
  <ElTooltip :content="tip" placement="bottom" raw-content>
    <ElTag size="small" :type="tagType">
      runtime: {{ runtime }}{{ fallback ? '（Pi 降级）' : '' }}
    </ElTag>
  </ElTooltip>
</template>
