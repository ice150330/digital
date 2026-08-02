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
import SessionList from '../components/SessionList.vue'
import ToolTimeline from '../components/ToolTimeline.vue'
import { useAgentStore } from '../stores/agent'

const agentStore = useAgentStore()
const { currentSessionId, messages, sessions, loading, streaming, error, runtime } = storeToRefs(agentStore)
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
            <ElOption label="本地工具" value="local" />
            <ElOption label="模板模式" value="template" />
          </ElSelect>
        </div>
      </template>
    </PageHeaderBar>

    <DisclaimerBanner content="LLM 只负责组织问题和说明结果，所有指标与图表数据均来自后端工具；Pi 不可用时会明确降级到本地工具。" />

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
        <header class="conversation-head">
          <div>
            <strong>{{ currentSessionId ? '当前分析会话' : '新分析会话' }}</strong>
            <span v-if="currentSessionId" class="session-id">{{ currentSessionId }}</span>
          </div>
          <span class="grounded-label"><Icon icon="uil:shield-check" size="sm" /> 工具接地</span>
        </header>

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
        <div class="monitor-head">
          <div><strong>工具监控</strong><span>本轮真实执行轨迹</span></div>
          <span class="monitor-count">{{ activeTrace.length }}</span>
        </div>
        <ToolTimeline :trace="activeTrace" :streaming="streaming" @retry="agentStore.retryTool" />
        <div class="runtime-card">
          <div class="runtime-card-title"><Icon icon="uil:processor" size="sm" /><strong>运行状态</strong></div>
          <dl>
            <div><dt>Runtime</dt><dd>{{ runtime }}</dd></div>
            <div><dt>Pi</dt><dd>{{ pi?.installed && !pi?.is_stub ? '已就绪' : '可降级' }}</dd></div>
            <div><dt>会话</dt><dd>{{ pi?.sessions_count ?? sessions.length }}</dd></div>
          </dl>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.agent-page { display: flex; flex-direction: column; gap: var(--space-4); }
.runtime-actions { display: flex; align-items: center; gap: var(--space-2); }
.runtime-select { width: 148px; }
.agent-workspace { display: grid; grid-template-columns: 248px minmax(0, 1fr) 304px; gap: var(--space-4); min-height: 680px; }
.conversation-panel { display: flex; min-width: 0; flex-direction: column; gap: var(--space-3); }
.conversation-head { display: flex; align-items: center; justify-content: space-between; min-height: 52px; padding: 0 var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-card); }
.conversation-head strong { color: var(--text-title); font-size: var(--font-size-md); }
.session-id { display: block; max-width: 240px; margin-top: var(--space-1); overflow: hidden; color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); text-overflow: ellipsis; white-space: nowrap; }
.grounded-label { display: inline-flex; align-items: center; gap: var(--space-1); color: var(--color-success-text); font-size: var(--font-size-xs); }
.message-list { display: flex; min-height: 380px; max-height: 660px; flex: 1; flex-direction: column; gap: var(--space-6); overflow-y: auto; padding: var(--space-5); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-subtle); scroll-behavior: smooth; }
.welcome-state { display: grid; min-height: 300px; place-items: center; align-content: center; text-align: center; }
.welcome-icon { display: grid; width: 56px; height: 56px; place-items: center; border-radius: var(--radius-full); background: var(--color-primary-50); color: var(--color-primary-600); }
.welcome-state h2 { margin: var(--space-3) 0 var(--space-1); color: var(--text-title); font-size: var(--font-size-xl); }
.welcome-state p { margin: 0; color: var(--text-secondary); font-size: var(--font-size-sm); }
.agent-error { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); border: 1px solid var(--color-danger-border); border-radius: var(--radius-md); background: var(--color-danger-bg); color: var(--color-danger-text); font-size: var(--font-size-sm); }
.monitor-panel { display: flex; flex-direction: column; gap: var(--space-3); }
.monitor-head { display: flex; align-items: center; justify-content: space-between; min-height: 52px; padding: 0 var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-card); }
.monitor-head strong, .monitor-head span { display: block; }
.monitor-head strong { color: var(--text-title); font-size: var(--font-size-sm); }
.monitor-head div > span { margin-top: var(--space-1); color: var(--text-secondary); font-size: var(--font-size-xs); }
.monitor-count { display: grid; width: 28px; height: 28px; place-items: center; border-radius: var(--radius-full); background: var(--color-primary-50); color: var(--color-primary-700); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
.runtime-card { padding: var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-card); }
.runtime-card-title { display: flex; align-items: center; gap: var(--space-2); color: var(--text-title); font-size: var(--font-size-sm); }
.runtime-card dl { margin: var(--space-3) 0 0; }
.runtime-card dl div { display: flex; justify-content: space-between; padding: var(--space-2) 0; border-top: 1px solid var(--border-default); font-size: var(--font-size-xs); }
.runtime-card dt { color: var(--text-secondary); }
.runtime-card dd { margin: 0; color: var(--text-title); font-family: var(--font-family-number); }
@media (max-width: 1280px) { .agent-workspace { grid-template-columns: 220px minmax(0, 1fr); } .monitor-panel { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 280px; } .monitor-head { grid-column: 1 / -1; } }
@media (max-width: 900px) { .agent-workspace { grid-template-columns: minmax(0, 1fr); } .monitor-panel { display: flex; } }
@media (max-width: 640px) {
  .runtime-actions { min-width: 0; width: 100%; }
  .runtime-select { width: auto; min-width: 0; flex: 1; }
  .agent-workspace { min-width: 0; min-height: 0; width: 100%; }
  .conversation-panel { order: 1; }
  .session-panel { order: 2; }
  .monitor-panel { order: 3; }
  .message-list { min-height: 320px; max-height: 520px; gap: var(--space-4); padding: var(--space-3); }
  .welcome-state { min-height: 240px; }
  .conversation-head { min-height: var(--control-height-lg); padding: 0 var(--space-3); }
}
</style>
