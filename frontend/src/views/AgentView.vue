<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElCollapse,
  ElCollapseItem,
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
import PageHeaderBar from '../components/PageHeaderBar.vue'

const message = ref('各渠道转化率如何？并给出模型 PR-AUC')
const loading = ref(false)
const error = ref<string | null>(null)
const sessionId = ref<string | undefined>()
const runtime = ref('template')
const history = ref<ChatData[]>([])
const pi = ref<PiStatusData | null>(null)
const chips = [
  '数据规模与正类占比',
  '各渠道转化率',
  '模型 PR-AUC 与 Dummy',
  '解释客户 8000',
  '质量问题有哪些',
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

onMounted(loadPi)
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="AI 分析台"
      description="工具接地 Copilot：数字来自 tool_trace；无 Key 时为 template/关键词模式。"
    >
      <template #actions>
        <ElSpace>
          <ElTag size="small" type="info">runtime: {{ runtime }}</ElTag>
          <ElSelect :model-value="runtime" style="width: 130px" @change="onRuntimeChange">
            <ElOption label="template" value="template" />
            <ElOption label="local" value="local" />
            <ElOption label="pi" value="pi" />
          </ElSelect>
        </ElSpace>
      </template>
    </PageHeaderBar>

    <p class="disclaimer">
      LLM 不替代主分类器；无工具结果不得编造 PR-AUC。Pi 仅允许
      <code>tools/pi-cli/</code>。
      <span v-if="pi">
        Pi：{{ pi.installed ? '已安装' : '未安装' }}
        <span v-if="pi.hint"> — {{ pi.hint }}</span>
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
          <ElTag size="small">{{ item.runtime }}</ElTag>
          <span class="mono muted">{{ item.session_id.slice(0, 8) }}…</span>
          <span v-if="item.latency_ms" class="muted">{{ item.latency_ms }} ms</span>
        </div>
        <pre class="reply">{{ item.reply }}</pre>
        <ElCollapse>
          <ElCollapseItem title="tool_trace" name="trace">
            <div v-for="(t, i) in item.tool_trace" :key="i" class="trace-item">
              <div>
                <ElTag :type="t.ok ? 'success' : 'danger'" size="small">{{ t.tool }}</ElTag>
                <span class="mono muted" style="margin-left: 8px">{{ JSON.stringify(t.args || {}) }}</span>
              </div>
              <pre v-if="t.error" class="err">{{ t.error }}</pre>
              <pre v-else class="json">{{ JSON.stringify(t.result, null, 2) }}</pre>
            </div>
          </ElCollapseItem>
          <ElCollapseItem title="observed_facts" name="facts">
            <ul>
              <li v-for="(f, i) in item.observed_facts" :key="i">{{ f }}</li>
            </ul>
          </ElCollapseItem>
        </ElCollapse>
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
  max-height: 520px;
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
.trace-item {
  margin-bottom: 10px;
}
.json,
.err {
  font-family: var(--font-mono);
  font-size: 11px;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 6px;
  overflow: auto;
  max-height: 200px;
}
.err {
  color: var(--color-danger);
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
