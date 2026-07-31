<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElInput,
  ElOption,
  ElSelect,
  ElSpace,
  ElTag,
} from 'element-plus'
import {
  chatAgent,
  fetchPiStatus,
  setRuntime,
  type ChatData,
  type PiStatusData,
} from '../api/agent'
import ChartCard, { type ChartSpec } from '../components/ChartCard.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import RuntimeBadge from '../components/RuntimeBadge.vue'
import ToolTracePanel from '../components/ToolTracePanel.vue'
import type { ToolTraceItem } from '../api/agent'

const message = ref('各渠道转化率如何？并给出模型 PR-AUC')
const loading = ref(false)
const error = ref<string | null>(null)
const sessionId = ref<string | undefined>()
const runtime = ref('pi')
const history = ref<ChatData[]>([])
const pi = ref<PiStatusData | null>(null)
const chips = [
  '数据规模与正类占比',
  '画各渠道转化率柱状图',
  '画实验矩阵 PR-AUC 对比图',
  '画分群规模占比饼图',
  '各渠道转化率',
  '模型 PR-AUC 与 Dummy',
  '对比各实验 PR-AUC 与置信区间',
  '校准前后差异',
  '预算 5000 的最优分配',
  '解释客户 8000',
  '反事实：客户 8000 怎样更可能转化',
  '分群画像摘要',
  '关联规则 lift 最高几条',
  '综合策略摘要',
]

async function loadPi() {
  try {
    const r = await fetchPiStatus()
    pi.value = r.data
  } catch {
    pi.value = null
  }
}

async function send(text?: string) {
  const msg = (text ?? message.value).trim()
  if (!msg) return
  loading.value = true
  error.value = null
  try {
    const res = await chatAgent({
      message: msg,
      session_id: sessionId.value,
      runtime: runtime.value,
    })
    sessionId.value = res.data.session_id
    history.value.push(res.data)
    message.value = ''
    await nextTick()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '对话失败'
  } finally {
    loading.value = false
  }
}

async function onRuntimeChange(v: string) {
  runtime.value = v
  try {
    await setRuntime(v)
  } catch {
    /* 本地演示：切换失败不阻塞聊天 */
  }
}

/** 从一轮对话的 tool_trace 提取 render_chart 成功结果（chart-spec v1.0）。 */
function chartSpecs(item: ChatData): ChartSpec[] {
  return (item.tool_trace || [])
    .filter((t: ToolTraceItem) => t.tool === 'render_chart' && t.ok && t.result)
    .map((t: ToolTraceItem) => t.result as ChartSpec)
}

onMounted(loadPi)
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="AI 分析台"
      description="工具接地 Copilot：数字来自 tool_trace；Pi 为默认编排 runtime，stub/未安装时明确降级。"
    >
      <template #actions>
        <ElSpace>
          <RuntimeBadge :runtime="runtime" :pi="pi" />
          <ElSelect :model-value="runtime" style="width: 130px" @change="onRuntimeChange">
            <ElOption label="pi（默认）" value="pi" />
            <ElOption label="local" value="local" />
            <ElOption label="template" value="template" />
          </ElSelect>
        </ElSpace>
      </template>
    </PageHeaderBar>

    <p class="disclaimer">
      LLM 不替代主分类器；无工具结果不得编造 PR-AUC。Pi 仅允许
      <code>tools/pi-cli/</code>。
      <span v-if="pi">
        Pi：{{ pi.installed ? (pi.is_stub ? 'stub 占位（降级 local）' : '已安装') : '未安装' }}
        <span v-if="pi.fallback_reason"> — {{ pi.fallback_reason }}</span>
        <span v-else-if="pi.hint"> — {{ pi.hint }}</span>
      </span>
    </p>

    <div class="chips">
      <ElButton
        v-for="c in chips"
        :key="c"
        size="small"
        round
        :disabled="loading"
        @click="send(c)"
      >
        {{ c }}
      </ElButton>
    </div>

    <ElCard shadow="never" class="section-card chat-panel">
      <div v-if="!history.length" class="muted empty-hint">发送问题开始分析，结果将展示五段契约与 tool_trace。</div>
      <div v-for="(item, idx) in history" :key="idx" class="turn">
        <div class="meta">
          <RuntimeBadge :runtime="item.runtime" :pi="pi" :fallback="item.pi_fallback" />
          <ElTag v-if="item.pi_fallback" size="small" type="warning">Pi 降级</ElTag>
          <span class="mono muted">{{ item.session_id.slice(0, 8) }}…</span>
          <span v-if="item.latency_ms" class="muted">{{ item.latency_ms }} ms</span>
        </div>
        <pre class="reply">{{ item.reply }}</pre>

        <div v-if="item.observed_facts.length" class="section">
          <div class="section-title">observed_facts（观察事实）</div>
          <ul><li v-for="(f, i) in item.observed_facts" :key="i">{{ f }}</li></ul>
        </div>
        <div v-if="item.inferences.length" class="section">
          <div class="section-title">inferences（推断）</div>
          <ul><li v-for="(f, i) in item.inferences" :key="i">{{ f }}</li></ul>
        </div>
        <div v-if="item.recommendations.length" class="section">
          <div class="section-title">recommendations（建议）</div>
          <ul><li v-for="(f, i) in item.recommendations" :key="i">{{ f }}</li></ul>
        </div>
        <div v-if="item.open_questions.length" class="section">
          <div class="section-title">open_questions（待澄清）</div>
          <ul><li v-for="(f, i) in item.open_questions" :key="i">{{ f }}</li></ul>
        </div>

        <!-- Stage 4：render_chart 工具结果内联渲染（数字来自宿主工具，非 LLM 生成） -->
        <ChartCard v-for="(spec, ci) in chartSpecs(item)" :key="ci" :spec="spec" />

        <ToolTracePanel :trace="item.tool_trace" />
      </div>
    </ElCard>

    <div v-if="error" class="err-bar">{{ error }}</div>

    <div class="composer">
      <ElInput
        v-model="message"
        type="textarea"
        :rows="2"
        placeholder="例如：客户 8000 的转化概率与局部解释"
        @keydown.ctrl.enter="send()"
      />
      <ElButton type="primary" :loading="loading" @click="send()">发送</ElButton>
    </div>
  </div>
</template>

<style scoped>
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.chat-panel {
  min-height: 280px;
  max-height: 560px;
  overflow: auto;
}
.empty-hint {
  padding: 24px;
  text-align: center;
}
.turn {
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}
.meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}
.reply {
  white-space: pre-wrap;
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.6;
  margin: 0 0 8px;
}
.section {
  margin: 8px 0;
}
.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}
.section ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}
.composer {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  margin-top: 12px;
  align-items: start;
}
.err-bar {
  color: var(--color-danger);
  font-size: 13px;
  margin-top: 8px;
}
</style>
