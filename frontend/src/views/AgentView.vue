<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElOption, ElSelect } from 'element-plus'
import { fetchPiStatus, setRuntime, type PiStatusData } from '../api/agent'
import AgentComposer from '../components/AgentComposer.vue'
import AgentMessage from '../components/AgentMessage.vue'
import AgentWorkspace from '../components/AgentWorkspace.vue'
import DisclaimerBanner from '../components/DisclaimerBanner.vue'
import Icon from '../components/Icon.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import RuntimeBadge from '../components/RuntimeBadge.vue'
import SessionList from '../components/SessionList.vue'
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
const focusedId = ref<string | null>(null)
const chips = [
  '各渠道转化率',
  '实验矩阵 PR-AUC 对比',
  '客户 8000 的转化解释',
  '预算 5000 如何分配',
  '分群画像摘要',
]

const latestAssistant = computed(() => [...messages.value].reverse().find((item) => item.role === 'assistant' && item.data))
const focusedAssistant = computed(() => (focusedId.value
  ? messages.value.find((item) => item.id === focusedId.value && item.role === 'assistant')
  : undefined) || latestAssistant.value || null)
const activeTrace = computed(() => focusedAssistant.value?.data?.tool_trace || [])
const monitorItems = computed(() => [
  { label: '工具', value: String(streaming.value ? completedToolCount.value : activeTrace.value.filter((item) => item.ok !== undefined).length) },
  { label: '图表', value: String(chartCount.value || activeTrace.value.filter((item) => item.tool === 'render_chart' && item.ok).length) },
  { label: '事件', value: String(eventCount.value) },
])

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
  focusedId.value = null
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
  focusedId.value = null
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
    <PageHeaderBar title="AI 分析台" description="自然语言对话式分析；指标、图表与每一步依据均来自后端工具结果。">
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

      <section class="chat-panel">
        <div ref="chatScroll" class="message-list" aria-live="polite">
          <div v-if="!messages.length" class="welcome-state">
            <div class="welcome-icon"><Icon icon="uil:robot" size="lg" /></div>
            <h2>从一个数据问题开始</h2>
            <p>可以询问渠道转化、模型指标、客户解释、分群画像或预算模拟。</p>
          </div>
          <AgentMessage
            v-for="item in messages"
            :key="item.id"
            :message="item"
            :focused="item.id === focusedId"
            @focus="focusedId = $event"
            @regenerate="send('请重新生成刚才的图表，并保留原有口径说明。')"
          />
        </div>

        <div v-if="error" class="agent-error" role="alert"><Icon icon="uil:exclamation-triangle" size="sm" />{{ error }}</div>
        <AgentComposer v-model="message" :loading="loading" :streaming="streaming" :chips="chips" @send="send" @stop="agentStore.stopStreaming" />
      </section>

      <AgentWorkspace
        class="workspace-panel"
        :data="focusedAssistant?.data ?? null"
        :phase="runPhase"
        :status-text="runStatusText"
        :active-tool="activeTool"
        :runtime="runtime"
        :session-count="pi?.sessions_count ?? sessions.length"
        :last-event-at="lastEventAt"
        :streaming="streaming"
        :monitor-items="monitorItems"
        @retry="agentStore.retryTool"
      />
    </div>
  </div>
</template>

<style scoped>
.agent-page { display: flex; flex-direction: column; gap: var(--space-3); }
.runtime-actions { display: flex; align-items: center; gap: var(--space-2); }
.runtime-select { width: 148px; }
.agent-workspace { display: grid; grid-template-columns: 236px minmax(0, 1fr) 300px; align-items: start; gap: var(--space-3); }
.session-panel { align-self: start; }
.chat-panel { display: flex; min-width: 0; flex-direction: column; gap: var(--space-3); }
.message-list { display: flex; min-height: 380px; max-height: 72vh; flex-direction: column; gap: var(--space-4); overflow-y: auto; padding: var(--space-1) var(--space-1) var(--space-4); scroll-behavior: smooth; }
.welcome-state { display: grid; min-height: 300px; place-items: center; align-content: center; text-align: center; }
.welcome-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: var(--radius-sm); background: var(--color-primary-50); color: var(--color-primary-600); }
.welcome-state h2 { margin: var(--space-3) 0 var(--space-1); color: var(--text-title); font-size: var(--font-size-xl); }
.welcome-state p { margin: 0; color: var(--text-secondary); font-size: var(--font-size-sm); }
.agent-error { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border: 1px solid var(--color-danger-border); border-radius: var(--radius-md); background: var(--color-danger-bg); color: var(--color-danger-text); font-size: var(--font-size-sm); }
@media (max-width: 1280px) {
  .agent-workspace { grid-template-columns: 220px minmax(0, 1fr); }
  .workspace-panel { grid-column: 1 / -1; }
}
@media (max-width: 992px) {
  .agent-workspace { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 640px) {
  .runtime-actions { min-width: 0; width: 100%; }
  .runtime-select { width: auto; min-width: 0; flex: 1; }
  .agent-workspace { min-width: 0; width: 100%; }
  .chat-panel { order: 1; }
  .session-panel { order: 2; }
  .workspace-panel { order: 3; }
  .message-list { min-height: 320px; max-height: 60vh; gap: var(--space-3); padding: var(--space-1) 0 var(--space-3); }
  .welcome-state { min-height: 240px; }
}
</style>
