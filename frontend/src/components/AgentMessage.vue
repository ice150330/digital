<script setup lang="ts">
import { computed } from 'vue'
import type { AgentUiMessage } from '../stores/agent'
import type { ToolTraceItem } from '../api/agent'
import ChartCard, { type ChartSpec } from './ChartCard.vue'
import Icon from './Icon.vue'
import MarkdownContent from './MarkdownContent.vue'
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
        <Tag v-if="message.data?.llm_model" tone="primary">{{ message.data.llm_model }}</Tag>
        <span v-if="message.data?.latency_ms" class="latency">{{ Math.round(message.data.latency_ms) }} ms</span>
      </div>
      <div class="message-content">
        <MarkdownContent :content="message.content" />
        <span v-if="message.streaming" class="typing-cursor" />
      </div>

      <div v-if="sections.length && !message.streaming" class="contract-folds" aria-label="分析契约详情">
        <details v-for="section in sections" :key="section.key" class="contract-fold">
          <summary>
            <span class="contract-title"><Icon :icon="section.icon" size="sm" />{{ section.title }}</span>
            <span class="contract-count">{{ section.items.length }} 条</span>
            <Icon class="contract-chevron" icon="uil:angle-down" size="sm" />
          </summary>
          <ul>
            <li v-for="(item, index) in section.items" :key="`${section.key}-${index}`">{{ item }}</li>
          </ul>
        </details>
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
.message-content { padding: var(--space-3) var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--bg-card); color: var(--text-body); font-size: var(--font-size-md); line-height: 1.7; box-shadow: var(--shadow-xs); }
.role-user .message-content { border-color: var(--color-primary-100); background: var(--color-primary-50); color: var(--color-primary-700); }
.typing-cursor { display: inline-block; width: 2px; height: 1em; margin-left: var(--space-1); background: var(--color-primary-500); vertical-align: -0.15em; animation: blink 0.8s steps(2, start) infinite; }
.contract-folds { display: grid; gap: var(--space-2); margin-top: var(--space-3); }
.contract-fold { overflow: hidden; border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--bg-card); box-shadow: var(--shadow-xs); }
.contract-fold summary { display: flex; align-items: center; gap: var(--space-2); min-height: 42px; padding: 0 var(--space-3); color: var(--text-title); cursor: pointer; list-style: none; }
.contract-fold summary::-webkit-details-marker { display: none; }
.contract-title { display: inline-flex; min-width: 0; flex: 1; align-items: center; gap: var(--space-2); overflow: hidden; font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); text-overflow: ellipsis; white-space: nowrap; }
.contract-count { display: inline-flex; align-items: center; min-height: var(--tag-height-sm); padding: 0 var(--space-2); border-radius: var(--radius-full); background: var(--bg-subtle); color: var(--text-secondary); font-size: var(--font-size-xs); white-space: nowrap; }
.contract-chevron { flex: 0 0 auto; color: var(--text-secondary); transition: transform var(--motion-duration-fast) var(--motion-easing-default); }
.contract-fold[open] .contract-chevron { transform: rotate(180deg); }
.contract-fold ul { margin: 0; padding: var(--space-3) var(--space-4) var(--space-3) var(--space-6); border-top: 1px solid var(--border-default); color: var(--text-body); font-size: var(--font-size-sm); line-height: 1.6; }
.contract-fold li + li { margin-top: var(--space-2); }
.message-charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: var(--space-3); margin-top: var(--space-3); }
@keyframes blink { 50% { opacity: 0; } }
@media (max-width: 992px) { .role-user .message-body { max-width: 100%; } }
@media (prefers-reduced-motion: reduce) { .typing-cursor { animation: none; } }
</style>
