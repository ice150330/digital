<script setup lang="ts">
import { computed } from 'vue'
import type { AgentUiMessage } from '../stores/agent'
import type { ToolTraceItem } from '../api/agent'
import ChartCard, { type ChartSpec } from './ChartCard.vue'
import Icon from './Icon.vue'
import MarkdownContent from './MarkdownContent.vue'

const props = defineProps<{ message: AgentUiMessage; focused?: boolean }>()
const emit = defineEmits<{
  regenerate: [spec: ChartSpec]
  focus: [id: string]
}>()

const chartSpecs = computed(() => (props.message.data?.tool_trace || [])
  .filter((item: ToolTraceItem) => item.tool === 'render_chart' && item.ok && item.result)
  .map((item: ToolTraceItem) => item.result as ChartSpec))

const toolCount = computed(() => props.message.data?.tool_trace?.length ?? 0)
const insightCount = computed(() => {
  const d = props.message.data
  if (!d) return 0
  return (d.observed_facts?.length ?? 0)
    + (d.inferences?.length ?? 0)
    + (d.recommendations?.length ?? 0)
    + (d.open_questions?.length ?? 0)
})
const hasData = computed(() => Boolean(props.message.data && (toolCount.value || insightCount.value)))
const latencyMs = computed(() => (props.message.data?.latency_ms != null ? Math.round(props.message.data.latency_ms) : null))
</script>

<template>
  <article class="agent-message" :class="[`role-${message.role}`, { focused }]">
    <div class="avatar"><Icon :icon="message.role === 'user' ? 'uil:user' : 'uil:robot'" size="md" /></div>
    <div class="message-body">
      <div class="message-meta">
        <strong>{{ message.role === 'user' ? '你' : '分析 Copilot' }}</strong>
        <span v-if="message.data?.pi_fallback" class="fallback-tag">Pi 降级</span>
      </div>

      <div class="message-content">
        <MarkdownContent :content="message.content" />
        <span v-if="message.streaming" class="typing-cursor" />
      </div>

      <div v-if="chartSpecs.length && !message.streaming" class="message-charts">
        <ChartCard v-for="(spec, index) in chartSpecs" :key="`${spec.title}-${index}`" :spec="spec" allow-zoom @regenerate="emit('regenerate', spec)" />
      </div>

      <div v-if="message.role === 'assistant' && !message.streaming && hasData" class="message-footer">
        <button type="button" class="focus-link" :class="{ active: focused }" @click="emit('focus', message.id)">
          <Icon :icon="focused ? 'uil:check-circle' : 'uil:arrow-right'" size="sm" />
          {{ focused ? '已聚焦' : '查看依据' }}
        </button>
        <span class="footer-meta">{{ toolCount }} 工具 · {{ insightCount }} 洞察</span>
        <span v-if="message.data?.llm_model" class="footer-meta model">{{ message.data.llm_model }}</span>
        <span v-if="latencyMs != null" class="footer-meta">{{ latencyMs }} ms</span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.agent-message { display: flex; align-items: flex-start; gap: var(--space-3); }
.agent-message.focused { position: relative; }
.avatar { display: grid; width: 28px; height: 28px; flex: 0 0 auto; place-items: center; border-radius: var(--radius-sm); background: var(--color-primary-50); color: var(--color-primary-700); }
.role-user { flex-direction: row-reverse; }
.role-user .avatar { background: var(--bg-subtle); color: var(--text-secondary); }
.message-body { min-width: 0; max-width: min(100%, 840px); }
.role-user .message-body { max-width: min(78%, 720px); }
.message-meta { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-1); color: var(--text-secondary); font-size: var(--font-size-xs); }
.message-meta strong { color: var(--text-title); font-size: var(--font-size-sm); }
.role-user .message-meta { justify-content: flex-end; }
.fallback-tag { padding: 0 var(--space-1); border-radius: var(--radius-sm); background: var(--color-warning-bg); color: var(--color-warning-text); font-size: var(--font-size-xs); }
.message-content { padding: var(--space-2) var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--bg-card); color: var(--text-body); font-size: var(--font-size-sm); line-height: 1.7; }
.role-user .message-content { border-color: var(--color-primary-100); background: var(--color-primary-50); color: var(--color-primary-700); }
.typing-cursor { display: inline-block; width: 2px; height: 1em; margin-left: var(--space-1); background: var(--color-primary-500); vertical-align: -0.15em; animation: blink 0.8s steps(2, start) infinite; }
.message-charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: var(--space-3); margin-top: var(--space-2); }
.message-footer { display: flex; align-items: center; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-2); color: var(--text-secondary); font-size: var(--font-size-xs); }
.focus-link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: 22px; padding: 0 var(--space-2); border: 1px solid var(--color-primary-100); border-radius: var(--radius-sm); background: var(--color-primary-50); color: var(--color-primary-700); cursor: pointer; font-size: var(--font-size-xs); }
.focus-link:hover { border-color: var(--color-primary-300); background: var(--color-primary-100); }
.focus-link.active { background: var(--color-primary-500); border-color: var(--color-primary-500); color: #fff; }
.footer-meta { display: inline-flex; align-items: center; }
.footer-meta.model { max-width: 220px; overflow: hidden; font-family: var(--font-family-code); text-overflow: ellipsis; white-space: nowrap; }
@keyframes blink { 50% { opacity: 0; } }
@media (max-width: 992px) { .role-user .message-body { max-width: 100%; } }
@media (prefers-reduced-motion: reduce) { .typing-cursor { animation: none; } }
</style>
