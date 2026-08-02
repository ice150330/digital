<script setup lang="ts">
import { computed } from 'vue'
import type { AgentUiMessage } from '../stores/agent'
import type { ToolTraceItem } from '../api/agent'
import ChartCard, { type ChartSpec } from './ChartCard.vue'
import Icon from './Icon.vue'
import Tag from './Tag.vue'

const props = defineProps<{ message: AgentUiMessage }>()
const emit = defineEmits<{ regenerate: [spec: ChartSpec] }>()
const chartSpecs = computed(() => (props.message.data?.tool_trace || [])
  .filter((item: ToolTraceItem) => item.tool === 'render_chart' && item.ok && item.result)
  .map((item: ToolTraceItem) => item.result as ChartSpec))
const sections = computed(() => {
  const data = props.message.data
  if (!data) return []
  return [
    { key: 'facts', title: '观察到的事实', icon: 'uil:database', items: data.observed_facts },
    { key: 'inferences', title: '可以怎样理解', icon: 'uil:lightbulb-alt', items: data.inferences },
    { key: 'recommendations', title: '建议下一步', icon: 'uil:compass', items: data.recommendations },
    { key: 'questions', title: '还需要确认', icon: 'uil:question-circle', items: data.open_questions },
  ].filter((section) => section.items?.length)
})
</script>

<template>
  <article class="agent-message" :class="`role-${message.role}`">
    <div class="avatar"><Icon :icon="message.role === 'user' ? 'uil:user' : 'uil:robot'" size="md" /></div>
    <div class="message-body">
      <div class="message-meta">
        <strong>{{ message.role === 'user' ? '你' : '分析 Copilot' }}</strong>
        <Tag v-if="message.data?.pi_fallback" tone="warning">Pi 已降级</Tag>
        <Tag v-if="message.data?.runtime" tone="info">{{ message.data.runtime }}</Tag>
        <span v-if="message.data?.latency_ms" class="latency">{{ Math.round(message.data.latency_ms) }} ms</span>
      </div>
      <div class="message-content">{{ message.content }}<span v-if="message.streaming" class="typing-cursor" /></div>

      <div v-if="sections.length && !message.streaming" class="contract-sections">
        <section v-for="section in sections" :key="section.key" class="contract-section">
          <h4><Icon :icon="section.icon" size="sm" />{{ section.title }}</h4>
          <ul><li v-for="item in section.items" :key="item">{{ item }}</li></ul>
        </section>
      </div>

      <div v-if="chartSpecs.length && !message.streaming" class="message-charts">
        <ChartCard v-for="(spec, index) in chartSpecs" :key="`${spec.title}-${index}`" :spec="spec" allow-zoom @regenerate="emit('regenerate', spec)" />
      </div>
    </div>
  </article>
</template>

<style scoped>
.agent-message { display: flex; align-items: flex-start; gap: var(--space-3); }
.avatar { display: grid; width: 36px; height: 36px; flex: 0 0 auto; place-items: center; border-radius: var(--radius-full); background: var(--color-primary-50); color: var(--color-primary-700); }
.role-user { flex-direction: row-reverse; }
.role-user .avatar { background: var(--bg-subtle); color: var(--text-secondary); }
.message-body { min-width: 0; max-width: min(100%, 860px); }
.role-user .message-body { max-width: min(78%, 720px); }
.message-meta { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-2); color: var(--text-secondary); font-size: var(--font-size-xs); }
.message-meta strong { color: var(--text-title); font-size: var(--font-size-sm); }
.role-user .message-meta { justify-content: flex-end; }
.latency { font-family: var(--font-family-number); }
.message-content { padding: var(--space-3) var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--bg-card); color: var(--text-body); font-size: var(--font-size-md); line-height: 1.7; white-space: pre-wrap; box-shadow: var(--shadow-xs); }
.role-user .message-content { border-color: var(--color-primary-100); background: var(--color-primary-50); color: var(--color-primary-700); }
.typing-cursor { display: inline-block; width: 2px; height: 1em; margin-left: var(--space-1); background: var(--color-primary-500); vertical-align: -0.15em; animation: blink 0.8s steps(2, start) infinite; }
.contract-sections { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin-top: var(--space-3); }
.contract-section { padding: var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--bg-card); }
.contract-section h4 { display: flex; align-items: center; gap: var(--space-2); margin: 0 0 var(--space-2); color: var(--text-title); font-size: var(--font-size-sm); }
.contract-section ul { margin: 0; padding-left: var(--space-5); color: var(--text-body); font-size: var(--font-size-sm); line-height: 1.6; }
.message-charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: var(--space-3); margin-top: var(--space-3); }
@keyframes blink { 50% { opacity: 0; } }
@media (max-width: 900px) { .contract-sections { grid-template-columns: 1fr; } .role-user .message-body { max-width: 100%; } }
@media (prefers-reduced-motion: reduce) { .typing-cursor { animation: none; } }
</style>
