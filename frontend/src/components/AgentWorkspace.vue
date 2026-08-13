<script setup lang="ts">
/**
 * /agent 右侧分栏工作区（Data Dense v3 紧凑型）。
 * 承载三块：运行状态（实时 phase / 工具 / 图表 / 事件 + runtime·模型·会话）、
 * 洞察（四段契约默认折叠，非必须汇报）、工具执行时间线。
 * 内容随「聚焦的助手消息」联动，聚焦缺省回落到最新一条助手回复。
 */
import { computed } from 'vue'
import type { ChatData, ToolTraceItem } from '../api/agent'
import Icon from './Icon.vue'
import SectionCard from './SectionCard.vue'
import ToolTimeline from './ToolTimeline.vue'

const props = defineProps<{
  data: ChatData | null
  phase: string
  statusText: string
  activeTool: string | null
  runtime: string
  sessionCount: number
  lastEventAt: string | null
  streaming?: boolean
  monitorItems: Array<{ label: string; value: string }>
}>()
const emit = defineEmits<{ retry: [item: ToolTraceItem] }>()

const trace = computed(() => props.data?.tool_trace || [])

const sections = computed(() => {
  const data = props.data
  if (!data) return []
  return [
    { key: 'facts', title: '观察到的事实', icon: 'uil:database', items: data.observed_facts },
    { key: 'inferences', title: '可以怎样理解', icon: 'uil:lightbulb-alt', items: data.inferences },
    { key: 'recommendations', title: '建议下一步', icon: 'uil:compass', items: data.recommendations },
    { key: 'questions', title: '还需要确认', icon: 'uil:question-circle', items: data.open_questions },
  ].filter((section) => section.items?.length)
})

const phaseLabel = computed(() => ({
  idle: '待命',
  planning: '规划中',
  bridge: '连接 Pi',
  tooling: '工具执行',
  replying: 'AI 回复',
  done: '已完成',
  error: '异常',
  stopped: '已停止',
}[props.phase] || props.phase))

const phaseTone = computed(() => {
  if (props.phase === 'done') return 'success'
  if (props.phase === 'error') return 'danger'
  if (props.phase === 'stopped') return 'warning'
  if (props.streaming) return 'primary'
  return 'info'
})

const idleHint = computed(() => (props.runtime === 'pi' ? 'Pi 编排 · 待命' : '上游 LLM · 待命'))
const modelLabel = computed(() => props.data?.llm_model || '—')
</script>

<template>
  <aside class="agent-workspace-panel">
    <SectionCard class="run-card" title="运行状态" :subtitle="statusText">
      <template #actions>
        <span class="run-phase" :class="`tone-${phaseTone}`">{{ phaseLabel }}</span>
      </template>
      <div class="run-state-main">
        <strong>{{ activeTool || (streaming ? '正在整理回复…' : idleHint) }}</strong>
        <small v-if="lastEventAt">{{ new Date(lastEventAt).toLocaleTimeString('zh-CN', { hour12: false }) }}</small>
      </div>
      <div class="run-state-grid">
        <div v-for="item in monitorItems" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
      <dl class="run-meta">
        <div><dt>Runtime</dt><dd>{{ runtime }}</dd></div>
        <div><dt>模型</dt><dd>{{ modelLabel }}</dd></div>
        <div><dt>会话</dt><dd>{{ sessionCount }}</dd></div>
      </dl>
    </SectionCard>

    <SectionCard class="insight-card" title="洞察" :subtitle="sections.length ? `${sections.length} 组 · 默认折叠` : undefined">
      <div v-if="sections.length" class="insight-list">
        <details v-for="section in sections" :key="section.key" class="insight-fold">
          <summary>
            <span class="insight-title"><Icon :icon="section.icon" size="sm" />{{ section.title }}</span>
            <span class="insight-count">{{ section.items.length }}</span>
            <Icon class="insight-chevron" icon="uil:angle-down" size="sm" />
          </summary>
          <ul>
            <li v-for="(item, index) in section.items" :key="`${section.key}-${index}`">{{ item }}</li>
          </ul>
        </details>
      </div>
      <p v-else class="insight-empty">本回复未产出结构化洞察，正文即为完整回答。</p>
    </SectionCard>

    <ToolTimeline :trace="trace" :streaming="streaming" @retry="emit('retry', $event)" />
  </aside>
</template>

<style scoped>
.agent-workspace-panel { display: flex; flex-direction: column; gap: var(--space-3); min-width: 0; }
.run-card { margin-bottom: 0; }
.run-phase { display: inline-flex; align-items: center; min-height: var(--tag-height-sm); padding: 0 var(--space-2); border-radius: var(--radius-sm); font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); white-space: nowrap; }
.tone-primary { color: var(--color-primary-700); background: var(--color-primary-50); }
.tone-success { color: var(--color-success-text); background: var(--color-success-bg); }
.tone-warning { color: var(--color-warning-text); background: var(--color-warning-bg); }
.tone-danger { color: var(--color-danger-text); background: var(--color-danger-bg); }
.tone-info { color: var(--text-secondary); background: var(--bg-subtle); }
.run-state-main { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); min-width: 0; }
.run-state-main strong { min-width: 0; overflow: hidden; color: var(--text-title); font-size: var(--font-size-sm); text-overflow: ellipsis; white-space: nowrap; }
.run-state-main small { color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); white-space: nowrap; }
.run-state-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-2); margin-top: var(--space-3); }
.run-state-grid div { min-width: 0; padding: var(--space-2); border-radius: var(--radius-md); background: var(--bg-subtle); }
.run-state-grid span { display: block; color: var(--text-secondary); font-size: var(--font-size-xs); }
.run-state-grid strong { display: block; margin-top: var(--space-1); color: var(--text-title); font-family: var(--font-family-number); font-size: var(--font-size-md); }
.run-meta { display: grid; gap: 0; margin: var(--space-3) 0 0; }
.run-meta div { display: flex; justify-content: space-between; padding: var(--space-1) 0; border-top: 1px solid var(--border-default); font-size: var(--font-size-xs); }
.run-meta dt { color: var(--text-secondary); }
.run-meta dd { margin: 0; min-width: 0; overflow: hidden; color: var(--text-title); font-family: var(--font-family-number); text-overflow: ellipsis; white-space: nowrap; }
.insight-card { margin-bottom: 0; }
.insight-list { display: grid; gap: var(--space-2); }
.insight-fold { overflow: hidden; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--bg-card); }
.insight-fold summary { display: flex; align-items: center; gap: var(--space-2); min-height: 30px; padding: 0 var(--space-2); color: var(--text-title); cursor: pointer; list-style: none; }
.insight-fold summary::-webkit-details-marker { display: none; }
.insight-title { display: inline-flex; min-width: 0; flex: 1; align-items: center; gap: var(--space-2); overflow: hidden; font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); text-overflow: ellipsis; white-space: nowrap; }
.insight-count { display: inline-flex; align-items: center; min-height: var(--tag-height-sm); padding: 0 var(--space-2); border-radius: var(--radius-sm); background: var(--bg-subtle); color: var(--text-secondary); font-size: var(--font-size-xs); white-space: nowrap; }
.insight-chevron { flex: 0 0 auto; color: var(--text-secondary); transition: transform var(--motion-duration-fast) var(--motion-easing-default); }
.insight-fold[open] .insight-chevron { transform: rotate(180deg); }
.insight-fold ul { margin: 0; padding: var(--space-2) var(--space-2) var(--space-2) var(--space-5); border-top: 1px solid var(--border-default); color: var(--text-body); font-size: var(--font-size-xs); line-height: 1.6; }
.insight-fold li + li { margin-top: var(--space-2); }
.insight-empty { margin: 0; color: var(--text-secondary); font-size: var(--font-size-xs); line-height: 1.6; }
@media (max-width: 1280px) {
  .agent-workspace-panel { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: start; }
}
@media (max-width: 992px) {
  .agent-workspace-panel { display: flex; }
}
</style>
