<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElOption, ElSelect } from 'element-plus'
import { fetchPiStatus, setRuntime, type PiStatusData } from '../api/agent'
import AgentComposer from '../components/AgentComposer.vue'
import AgentMessage from '../components/AgentMessage.vue'
import DisclaimerBanner from '../components/DisclaimerBanner.vue'
import Icon from '../components/Icon.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import RuntimeBadge from '../components/RuntimeBadge.vue'
import SectionCard from '../components/SectionCard.vue'
import SessionList from '../components/SessionList.vue'
import ToolTimeline from '../components/ToolTimeline.vue'
import { useAgentStore } from '../stores/agent'

const agentStore = useAgentStore()
const {
  currentSessionId,
  messages,
  sessions,
  loading,
  streaming,
  error,
  runtime,
  runPhase,
  runStatusText,
  activeTool,
  eventCount,
  completedToolCount,
  chartCount,
  lastEventAt,
} = storeToRefs(agentStore)
const message = ref('各渠道转化率如何？请生成柱状图并说明模型 PR-AUC。')
const pi = ref<PiStatusData | null>(null)
const chatScroll = ref<HTMLElement | null>(null)
const chips = [
  '各渠道转化率',
  '实验矩阵 PR-AUC 对比',
  '客户 8000 的转化解释',
  '预算 5000 如何分配',
  '分群画像摘要',
]

const latestAssistant = computed(() => [...messages.value].reverse().find((item) => item.role === 'assistant' && item.data))
const activeTrace = computed(() => latestAssistant.value?.data?.tool_trace || [])
const phaseLabel = computed(() => ({
  idle: '待命',
  planning: '规划中',
  bridge: '连接 Pi',
  tooling: '工具执行',
  replying: 'AI 回复',
  done: '已完成',
  error: '异常',
  stopped: '已停止',
}[runPhase.value] || runPhase.value))
const phaseTone = computed(() => {
  if (runPhase.value === 'done') return 'success'
  if (runPhase.value === 'error') return 'danger'
  if (runPhase.value === 'stopped') return 'warning'
  if (streaming.value || loading.value) return 'primary'
  return 'info'
})
const monitorItems = computed(() => [
  { label: '工具完成', value: String(streaming.value ? completedToolCount.value : activeTrace.value.filter((item) => item.ok !== undefined).length) },
  { label: '图表', value: String(chartCount.value || activeTrace.value.filter((item) => item.tool === 'render_chart' && item.ok).length) },
  { label: '事件', value: String(eventCount.value) },
])
const runtimeState = computed(() => {
  if (runtime.value === 'pi') {
    if (pi.value?.installed && !pi.value?.is_stub && pi.value?.bridge_ready) return 'Pi bridge ready'
    return 'Pi fallback guarded'
  }
  return '上游 LLM'
})

async function loadPi() {
  try {
    const response = await fetchPiStatus()
    pi.value = response.data
    runtime.value = response.data.default_runtime || 'pi'
  } catch {
    pi.value = null
  }
}

async function send(text?: string) {
  const content = (text || message.value).trim()
  if (!content) return
  if (!text) message.value = ''
  const pending = agentStore.sendMessage(content)
  await nextTick()
  chatScroll.value?.scrollTo({ top: chatScroll.value.scrollHeight, behavior: 'smooth' })
  await pending
  await nextTick()
  chatScroll.value?.scrollTo({ top: chatScroll.value.scrollHeight, behavior: 'smooth' })
}

async function changeRuntime(value: string) {
  runtime.value = value
  try {
    await setRuntime(value)
  } catch (cause) {
    agentStore.error = cause instanceof Error ? cause.message : 'Runtime 切换失败'
  }
}

async function selectSession(id: string) {
  await agentStore.loadSession(id)
  await nextTick()
  chatScroll.value?.scrollTo({ top: chatScroll.value.scrollHeight })
}

onMounted(() => {
  void agentStore.loadSessions()
  void loadPi()
})

watch(
  () => messages.value.map((item) => `${item.id}:${item.content.length}:${item.data?.tool_trace.length ?? 0}`).join('|'),
  async () => {
    await nextTick()
    chatScroll.value?.scrollTo({
      top: chatScroll.value.scrollHeight,
      behavior: streaming.value ? 'auto' : 'smooth',
    })
  },
)
</script>

<template>
  <div class="page agent-page">
    <PageHeaderBar title="AI 分析台" description="用自然语言调用分析工具，查看事实、解释、建议和每一步工具执行依据。">
      <template #actions>
        <div class="runtime-actions">
          <RuntimeBadge :runtime="runtime" :pi="pi" />
          <ElSelect class="runtime-select" :model-value="runtime" aria-label="选择 Agent Runtime" @change="changeRuntime">
            <ElOption label="Pi（默认）" value="pi" />
            <ElOption label="本地 LLM" value="local" />
          </ElSelect>
        </div>
      </template>
    </PageHeaderBar>

    <DisclaimerBanner content="AI 回复由上游模型生成；指标、转化率、SHAP 与图表数据只来自后端工具结果。" />

    <div class="agent-workspace">
      <SessionList
        class="session-panel"
        :sessions="sessions"
        :active-id="currentSessionId"
        :loading="loading && !messages.length"
        @create="agentStore.createSession"
        @select="selectSession"
        @delete="agentStore.deleteSession"
      />

      <section class="conversation-panel">
        <SectionCard class="conversation-head" title="当前分析会话" :subtitle="currentSessionId || undefined">
          <template #actions>
            <span class="grounded-label" :class="`tone-${phaseTone}`">
              <Icon icon="uil:shield-check" size="sm" /> {{ phaseLabel }}
            </span>
          </template>
        </SectionCard>

        <div ref="chatScroll" class="message-list" aria-live="polite">
          <div v-if="!messages.length" class="welcome-state">
            <div class="welcome-icon"><Icon icon="uil:robot" size="lg" /></div>
            <h2>从一个数据问题开始</h2>
            <p>可以询问渠道转化、模型指标、客户解释、分群画像或预算模拟。</p>
          </div>
          <AgentMessage v-for="item in messages" :key="item.id" :message="item" @regenerate="send('请重新生成刚才的图表，并保留原有口径说明。')" />
        </div>

        <div v-if="error" class="agent-error" role="alert"><Icon icon="uil:exclamation-triangle" size="sm" />{{ error }}</div>
        <AgentComposer v-model="message" :loading="loading" :streaming="streaming" :chips="chips" @send="send" @stop="agentStore.stopStreaming" />
      </section>

      <aside class="monitor-panel">
        <SectionCard class="monitor-head" title="运行监控" :subtitle="runStatusText">
          <template #actions>
            <span class="monitor-count">{{ activeTrace.length }}</span>
          </template>
        </SectionCard>
        <SectionCard class="run-state-card" title="执行状态">
          <div class="run-state-main">
            <span class="run-phase" :class="`tone-${phaseTone}`">{{ phaseLabel }}</span>
            <strong>{{ activeTool || runtimeState }}</strong>
            <small v-if="lastEventAt">{{ new Date(lastEventAt).toLocaleTimeString('zh-CN', { hour12: false }) }}</small>
          </div>
          <div class="run-state-grid">
            <div v-for="item in monitorItems" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </SectionCard>
        <ToolTimeline :trace="activeTrace" :streaming="streaming" @retry="agentStore.retryTool" />
        <SectionCard class="runtime-card" title="运行状态">
          <dl>
            <div><dt>Runtime</dt><dd>{{ runtime }}</dd></div>
            <div><dt>Pi</dt><dd>{{ pi?.installed && !pi?.is_stub ? '已就绪' : '可降级' }}</dd></div>
            <div><dt>模型</dt><dd>{{ latestAssistant?.data?.llm_model || '—' }}</dd></div>
            <div><dt>会话</dt><dd>{{ pi?.sessions_count ?? sessions.length }}</dd></div>
          </dl>
        </SectionCard>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.agent-page { display: flex; flex-direction: column; gap: var(--space-3); }
.runtime-actions { display: flex; align-items: center; gap: var(--space-2); }
.runtime-select { width: 148px; }
.agent-workspace { display: grid; grid-template-columns: 248px minmax(0, 1fr) 304px; align-items: start; gap: var(--space-3); min-height: 680px; }
.session-panel { align-self: start; }
.conversation-panel { display: flex; min-width: 0; flex-direction: column; gap: var(--space-3); }
.conversation-head { margin-bottom: 0; }
.conversation-head :deep(.section-card-title) { font-size: var(--font-size-md); }
.session-id { display: block; max-width: 240px; margin-top: var(--space-1); overflow: hidden; color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); text-overflow: ellipsis; white-space: nowrap; }
.grounded-label { display: inline-flex; align-items: center; gap: var(--space-1); padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm); background: var(--bg-subtle); color: var(--text-secondary); font-size: var(--font-size-xs); }
.tone-primary { color: var(--color-primary-700); background: var(--color-primary-50); }
.tone-success { color: var(--color-success-text); background: var(--color-success-bg); }
.tone-warning { color: var(--color-warning-text); background: var(--color-warning-bg); }
.tone-danger { color: var(--color-danger-text); background: var(--color-danger-bg); }
.tone-info { color: var(--text-secondary); background: var(--bg-subtle); }
.message-list { display: flex; min-height: 380px; max-height: 660px; flex: 1; flex-direction: column; gap: var(--space-3); overflow-y: auto; padding: var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-subtle); scroll-behavior: smooth; }
.welcome-state { display: grid; min-height: 300px; place-items: center; align-content: center; text-align: center; }
.welcome-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: var(--radius-sm); background: var(--color-primary-50); color: var(--color-primary-600); }
.welcome-state h2 { margin: var(--space-3) 0 var(--space-1); color: var(--text-title); font-size: var(--font-size-xl); }
.welcome-state p { margin: 0; color: var(--text-secondary); font-size: var(--font-size-sm); }
.agent-error { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border: 1px solid var(--color-danger-border); border-radius: var(--radius-md); background: var(--color-danger-bg); color: var(--color-danger-text); font-size: var(--font-size-sm); }
.monitor-panel { display: flex; flex-direction: column; gap: var(--space-3); }
.monitor-head { margin-bottom: 0; }
.monitor-count { display: grid; width: 28px; height: 28px; place-items: center; border-radius: var(--radius-sm); background: var(--color-primary-50); color: var(--color-primary-700); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
.run-state-card { margin-bottom: 0; }
.run-state-main { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--space-2); min-width: 0; }
.run-state-main strong { overflow: hidden; color: var(--text-title); font-size: var(--font-size-sm); text-overflow: ellipsis; white-space: nowrap; }
.run-state-main small { color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
.run-phase { display: inline-flex; align-items: center; min-height: 24px; padding: 0 var(--space-2); border-radius: var(--radius-sm); font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); white-space: nowrap; }
.run-state-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-2); margin-top: var(--space-3); }
.run-state-grid div { min-width: 0; padding: var(--space-2); border-radius: var(--radius-md); background: var(--bg-subtle); }
.run-state-grid span { display: block; color: var(--text-secondary); font-size: var(--font-size-xs); }
.run-state-grid strong { display: block; margin-top: var(--space-1); color: var(--text-title); font-family: var(--font-family-number); font-size: var(--font-size-md); }
.runtime-card { margin-bottom: 0; }
.runtime-card dl { margin: 0; }
.runtime-card dl div { display: flex; justify-content: space-between; padding: var(--space-2) 0; border-top: 1px solid var(--border-default); font-size: var(--font-size-xs); }
.runtime-card dt { color: var(--text-secondary); }
.runtime-card dd { margin: 0; color: var(--text-title); font-family: var(--font-family-number); }
@media (max-width: 1280px) { .agent-workspace { grid-template-columns: 220px minmax(0, 1fr); } .monitor-panel { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 280px; } .monitor-head { grid-column: 1 / -1; } }
@media (max-width: 992px) { .agent-workspace { grid-template-columns: minmax(0, 1fr); } .monitor-panel { display: flex; } }
@media (max-width: 640px) {
  .runtime-actions { min-width: 0; width: 100%; }
  .runtime-select { width: auto; min-width: 0; flex: 1; }
  .agent-workspace { min-width: 0; min-height: 0; width: 100%; }
  .conversation-panel { order: 1; }
  .session-panel { order: 2; }
  .monitor-panel { order: 3; }
  .message-list { min-height: 320px; max-height: 520px; gap: var(--space-3); padding: var(--space-2); }
  .welcome-state { min-height: 240px; }
  .conversation-head :deep(.section-card-title) { font-size: var(--font-size-sm); }
  .run-state-main { grid-template-columns: 1fr; align-items: start; }
}
</style>
