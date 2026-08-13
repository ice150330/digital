<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  ElButton, ElCard, ElCollapse, ElCollapseItem, ElDescriptions, ElDescriptionsItem, ElInput, ElSpace,
  ElMessage, ElTable, ElTableColumn, ElTag,
} from 'element-plus'
import {
  fetchAgentSession, fetchAuditRecent, fetchPiConfig, fetchPiModels, fetchToolsManifest, generateReport, updatePiConfig,
  type AuditRow, type PiAgentConfigData, type PiAgentConfigUpdate, type PiModelItemData, type PiStatusData, type ReportData, type ToolManifestItem,
} from '../api/agent'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import Icon from '../components/Icon.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import PiAgentConfigCard from '../components/PiAgentConfigCard.vue'
import RuntimeBadge from '../components/RuntimeBadge.vue'
import StatStrip from '../components/StatStrip.vue'
import ToolTracePanel from '../components/ToolTracePanel.vue'

type StatTone = 'primary' | 'success' | 'warning' | 'danger' | 'info'
type PiSummaryItem = { label: string; value: string; hint?: string; icon?: string; tone?: StatTone }

const loading = ref(false)
const error = ref<string | null>(null)
const configError = ref<string | null>(null)
const configSaving = ref(false)
const config = ref<PiAgentConfigData | null>(null)
const modelItems = ref<PiModelItemData[]>([])
const modelsLoading = ref(false)
const modelsError = ref<string | null>(null)
const pi = ref<PiStatusData | null>(null)
const audit = ref<AuditRow[]>([])

const reportLoading = ref(false)
const reportTitle = ref('数字营销转化分析报告')
const report = ref<ReportData | null>(null)

const sessionId = ref('')
const sessionData = ref<Record<string, unknown> | null>(null)
const sessionError = ref<string | null>(null)
const tools = ref<ToolManifestItem[]>([])
const toolsOpen = ref<string[]>([])
const toolsError = ref<string | null>(null)

const auditAggregates = computed(() => {
  const rows = audit.value
  if (!rows.length) return []
  const total = rows.length
  const totalMs = rows.reduce((sum, r) => sum + (r.latency_ms ?? 0), 0)
  const okCalls = rows.reduce((sum, r) => sum + (r.tool_calls?.filter((c) => c.ok).length ?? 0), 0)
  const totalCalls = rows.reduce((sum, r) => sum + (r.tool_calls?.length ?? 0), 0)
  const errors = rows.filter((r) => r.error).length
  return [
    { label: '审计条数', value: String(total), hint: '最近 50 条', icon: 'uil:file-alt', tone: 'info' as StatTone },
    { label: '平均延迟', value: `${Math.round(totalMs / total)} ms`, hint: '含 LLM 等待', icon: 'uil:clock', tone: 'primary' as StatTone },
    { label: '工具成功率', value: totalCalls ? `${((okCalls / totalCalls) * 100).toFixed(1)}%` : '—', hint: `${okCalls}/${totalCalls}`, icon: 'uil:check-circle', tone: 'success' as StatTone },
    { label: '错误条数', value: String(errors), hint: '审计级异常', icon: 'uil:exclamation-triangle', tone: (errors ? 'warning' : 'success') as StatTone },
  ]
})

async function load() {
  loading.value = true
  error.value = null
  configError.value = null
  try {
    const [c, a] = await Promise.all([fetchPiConfig(), fetchAuditRecent(50)])
    config.value = c.data
    pi.value = c.data.status
    audit.value = a.data.items
    void loadTools()
    if (c.data.config_endpoint_ready === false) {
      configError.value = '后端尚未加载 /agent/pi/config，当前为只读兼容状态；重启 API 后即可保存配置。'
      modelItems.value = []
      modelsError.value = '后端尚未加载 /agent/pi/models。'
    } else if (c.data.settings.llm.api_key_configured) {
      await loadModels()
    } else {
      modelItems.value = []
      modelsError.value = '保存 API Key 后可从上游获取模型列表。'
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadTools() {
  toolsError.value = null
  try {
    const r = await fetchToolsManifest()
    tools.value = r.data.tools
  } catch (e) {
    tools.value = []
    toolsError.value = e instanceof Error ? e.message : '工具清单获取失败'
  }
}

async function saveConfig(payload: PiAgentConfigUpdate) {
  if (config.value?.config_endpoint_ready === false) {
    configError.value = '后端尚未加载 /agent/pi/config，当前不能保存；请重启 API 后刷新本页。'
    return
  }
  configSaving.value = true
  configError.value = null
  try {
    const r = await updatePiConfig(payload)
    config.value = r.data
    pi.value = r.data.status
    if (r.data.settings.llm.api_key_configured) {
      await loadModels()
    } else {
      modelItems.value = []
      modelsError.value = '保存 API Key 后可从上游获取模型列表。'
    }
    ElMessage.success('PiAgent 配置已保存')
  } catch (e) {
    configError.value = e instanceof Error ? e.message : '配置保存失败'
  } finally {
    configSaving.value = false
  }
}

async function loadModels() {
  if (config.value?.config_endpoint_ready === false) {
    modelsError.value = '后端尚未加载 /agent/pi/models；请重启 API 后重试。'
    return
  }
  modelsLoading.value = true
  modelsError.value = null
  try {
    const r = await fetchPiModels()
    modelItems.value = r.data.models
    if (!r.data.models.length) modelsError.value = '上游未返回可用模型。'
  } catch (e) {
    modelItems.value = []
    modelsError.value = e instanceof Error ? e.message : '模型列表获取失败'
  } finally {
    modelsLoading.value = false
  }
}

async function makeReport() {
  reportLoading.value = true
  report.value = null
  try {
    const r = await generateReport({ title: reportTitle.value || undefined })
    report.value = r.data
  } catch (e) {
    error.value = e instanceof Error ? e.message : '报告生成失败'
  } finally {
    reportLoading.value = false
  }
}

async function replay() {
  sessionError.value = null
  sessionData.value = null
  if (!sessionId.value.trim()) return
  try {
    const r = await fetchAgentSession(sessionId.value.trim())
    sessionData.value = r.data
  } catch (e) {
    sessionError.value = e instanceof Error ? e.message : '会话不存在'
  }
}

onMounted(load)

const summaryItems = computed<PiSummaryItem[]>(() => {
  const st = pi.value
  const settings = config.value?.settings
  const installed = st?.installed && !st?.is_stub
  const bridgeReady = Boolean(st?.bridge_ready)
  return [
    {
      label: 'Runtime',
      value: settings?.runtime || st?.default_runtime || '—',
      hint: installed ? '项目内 Pi' : (st?.fallback_reason || st?.message || '可降级 local'),
      icon: 'uil:processor',
      tone: installed ? 'success' : 'warning',
    },
    {
      label: 'Bridge',
      value: bridgeReady ? 'ready' : 'pending',
      hint: st?.bridge_note || settings?.pi.bridge_model || 'SDK / node / script',
      icon: 'uil:bolt-alt',
      tone: bridgeReady ? 'success' : 'warning',
    },
    {
      label: 'Skills',
      value: String(st?.skills_detail?.length ?? 0),
      hint: settings?.pi.skills_dir || 'src/digital_marketing/agent/skills',
      icon: 'uil:brackets-curly',
      tone: 'primary',
    },
    {
      label: 'Audit',
      value: String(audit.value.length),
      hint: `${st?.sessions_count ?? 0} 个会话`,
      icon: 'uil:clipboard-notes',
      tone: 'info',
    },
  ]
})
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="Pi 编排中枢"
      description="PiAgent 的运行配置、健康诊断、skills、一键报告、会话回放与审计日志。"
    >
      <template #actions>
        <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
      </template>
    </PageHeaderBar>

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <StatStrip :items="summaryItems" class="pi-summary" />

    <PiAgentConfigCard
      :config="config"
      :loading="loading"
      :saving="configSaving"
      :error="configError"
      :models="modelItems"
      :models-loading="modelsLoading"
      :models-error="modelsError"
      @refresh="load"
      @refresh-models="loadModels"
      @save="saveConfig"
      class="config-section"
    />

    <div class="grid-2">
      <div>
        <ElCard shadow="never" class="section-card">
          <template #header>
            Runtime 健康
            <RuntimeBadge
              v-if="pi"
              :runtime="pi.installed && !pi.is_stub ? 'pi' : 'local'"
              :pi="pi"
              :fallback="Boolean(pi.is_stub || pi.fallback_reason)"
              class="ml-sm"
            />
          </template>
          <ElDescriptions v-if="pi" :column="1" size="small" border class="runtime-desc">
            <ElDescriptionsItem label="默认 runtime">
              <span class="mono">{{ pi.default_runtime }}</span>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="Bridge Model">
              <span class="mono">{{ config?.settings.pi.bridge_model || 'deepseek/deepseek-chat' }}</span>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="Base URL">
              <span class="mono">{{ config?.settings.llm.base_url || '默认 provider 地址' }}</span>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="API Key">
              <ElTag
                size="small"
                :type="config?.settings.llm.api_key_configured ? 'success' : 'info'"
              >
                {{ config?.settings.llm.api_key_configured ? config?.settings.llm.api_key_preview : '未配置' }}
              </ElTag>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="Pi 可执行文件">
              <span class="mono">{{ pi.executable || '未安装' }}</span>
              <ElTag v-if="pi.is_stub" size="small" type="warning">stub 占位</ElTag>
              <ElTag v-else-if="pi.installed" size="small" type="success">真实安装</ElTag>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="Pi SDK 桥接">
              <ElTag size="small" :type="pi.bridge_ready ? 'success' : 'warning'">
                {{ pi.bridge_ready ? '已就绪' : '未就绪' }}
              </ElTag>
              <span v-if="pi.bridge_note" class="muted ml-sm">{{ pi.bridge_note }}</span>
            </ElDescriptionsItem>
            <ElDescriptionsItem v-if="pi.fallback_reason" label="降级原因">
              {{ pi.fallback_reason }}
            </ElDescriptionsItem>
            <ElDescriptionsItem v-if="pi.hint" label="提示">{{ pi.hint }}</ElDescriptionsItem>
            <ElDescriptionsItem label="会话数">
              <span class="tabular-nums">{{ pi.sessions_count }}</span>
            </ElDescriptionsItem>
          </ElDescriptions>
          <p class="muted mb-0">
            Pi 仅允许 <code>tools/pi-cli/</code>（项目内）；禁止 PATH/which pi 回退与全局安装。
          </p>
        </ElCard>

        <ElCard shadow="never" class="section-card">
          <template #header>
            Skills（{{ pi?.skills_detail?.length ?? 0 }}）
          </template>
          <EmptyState
            v-if="!pi?.skills_detail?.length"
            title="未发现 skills"
            description="skills 目录：src/digital_marketing/agent/skills/*/SKILL.md"
          />
          <div v-for="s in pi?.skills_detail ?? []" :key="s.name" class="skill">
            <div class="skill-heading">
              <Icon icon="uil:brackets-curly" size="sm" color="var(--color-primary-600)" />
              <div class="skill-name mono">{{ s.name }}</div>
            </div>
            <div class="muted">{{ s.description }}</div>
          </div>
        </ElCard>

        <ElCard shadow="never" class="section-card">
          <template #header>一键分析报告</template>
          <ElSpace wrap class="w-full">
            <ElInput v-model="reportTitle" class="input-wide" placeholder="报告标题" />
            <ElButton type="primary" :loading="reportLoading" @click="makeReport">
              生成报告
            </ElButton>
          </ElSpace>
          <div v-if="report" class="report-box">
            <p>
              <ElTag size="small" :type="report.n_sections_ok === report.n_sections ? 'success' : 'warning'">
                {{ report.n_sections_ok }}/{{ report.n_sections }} 节完成
              </ElTag>
              <span class="mono muted ml-sm">{{ report.report_path }}</span>
            </p>
            <pre class="digest">{{ report.digest }}</pre>
            <ToolTracePanel :trace="report.tool_trace" />
            <p class="muted">{{ report.disclaimer }}</p>
          </div>
        </ElCard>
      </div>

      <div>
        <ElCard shadow="never" class="section-card">
          <template #header>会话回放</template>
          <ElSpace wrap class="w-full">
            <ElInput v-model="sessionId" class="input-wide" placeholder="session_id（见审计表）" />
            <ElButton @click="replay">加载</ElButton>
          </ElSpace>
          <p v-if="sessionError" class="err-text">{{ sessionError }}</p>
          <pre v-if="sessionData" class="json">{{ JSON.stringify(sessionData, null, 2) }}</pre>
          <EmptyState
            v-else-if="!sessionError"
            title="输入会话 ID"
            description="从右侧审计表复制 session_id 回放完整对话与工具轨迹。"
          />
        </ElCard>

        <ElCard shadow="never" class="section-card">
          <template #header>审计日志（最近 {{ audit.length }} 条）</template>
          <StatStrip :items="auditAggregates" class="mb-sm" />
          <ElCollapse v-model="toolsOpen">
            <ElCollapseItem title="工具清单" name="tools">
              <p v-if="toolsError" class="err-text">{{ toolsError }}</p>
              <div v-else-if="tools.length" class="tool-list">
                <div v-for="t in tools" :key="t.name" class="tool-item">
                  <span class="mono tool-name">{{ t.name }}</span>
                  <span class="muted">{{ t.description }}</span>
                </div>
              </div>
              <EmptyState v-else title="暂无工具清单" description="请确认 /agent/tools/manifest 已注册。" />
            </ElCollapseItem>
          </ElCollapse>
          <ElTable :data="audit" size="small" stripe max-height="520" class="mt-sm">
            <ElTableColumn label="时间" width="150">
              <template #default="{ row }"><span class="mono muted">{{ row.ts }}</span></template>
            </ElTableColumn>
            <ElTableColumn label="runtime" width="110">
              <template #default="{ row }">
                <ElTag size="small" :type="row.runtime === 'pi' ? 'success' : 'info'">{{ row.runtime }}</ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn label="用户消息" min-width="200">
              <template #default="{ row }">{{ row.user_message }}</template>
            </ElTableColumn>
            <ElTableColumn label="工具" min-width="160">
              <template #default="{ row }">
                <ElTag
                  v-for="(t, i) in row.tool_calls"
                  :key="i"
                  size="small"
                  :type="t.ok ? 'success' : 'danger'"
                  class="mr-xs"
                >
                  {{ t.tool }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn label="会话" width="110">
              <template #default="{ row }">
                <span class="mono muted">{{ row.session_id?.slice(0, 8) }}…</span>
              </template>
            </ElTableColumn>
            <ElTableColumn label="耗时" width="80">
              <template #default="{ row }">
                <span class="tabular-nums muted">{{ row.latency_ms ?? '—' }}ms</span>
              </template>
            </ElTableColumn>
          </ElTable>
        </ElCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pi-summary,
.config-section {
  margin-bottom: var(--space-3);
}
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: var(--space-3);
  align-items: start;
}
.grid-2 > * {
  min-width: 0;
}
@media (max-width: 992px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
.skill {
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--border-default);
}
.skill-heading {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}
.skill:last-child {
  border-bottom: none;
}
.skill-name {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
}
.tool-list { display: flex; flex-direction: column; gap: var(--space-2); }
.tool-item { display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-2) 0; border-bottom: 1px solid var(--border-default); }
.tool-item:last-child { border-bottom: none; }
.tool-name { color: var(--text-title); font-size: var(--font-size-sm); }
.report-box {
  margin-top: var(--space-3);
}
.digest {
  white-space: pre-wrap;
  font-family: var(--font-family-base);
  font-size: var(--font-size-xs);
  background: var(--color-code-bg);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  max-height: 220px;
  overflow: auto;
}
.json {
  font-family: var(--font-family-code);
  font-size: var(--font-size-xs);
  background: var(--color-code-bg);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  overflow: auto;
  max-height: 420px;
  margin-top: var(--space-3);
}
.err-text {
  color: var(--color-danger-text);
  font-size: var(--font-size-sm);
}
.runtime-desc :deep(.el-descriptions__label) {
  min-width: 104px;
  white-space: nowrap;
}
.runtime-desc :deep(.el-descriptions__table) {
  width: 100%;
  table-layout: fixed;
}
.runtime-desc :deep(.el-descriptions__content) {
  min-width: 0;
  overflow-wrap: anywhere;
}
.runtime-desc .mono {
  white-space: normal;
  word-break: break-all;
}
</style>
