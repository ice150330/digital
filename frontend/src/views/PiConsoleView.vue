<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ElButton, ElCard, ElDescriptions, ElDescriptionsItem, ElInput, ElSpace,
  ElTable, ElTableColumn, ElTag,
} from 'element-plus'
import {
  fetchAgentSession, fetchAuditRecent, fetchPiStatus, generateReport,
  type AuditRow, type PiStatusData, type ReportData,
} from '../api/agent'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import Icon from '../components/Icon.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import RuntimeBadge from '../components/RuntimeBadge.vue'
import ToolTracePanel from '../components/ToolTracePanel.vue'

const loading = ref(false)
const error = ref<string | null>(null)
const pi = ref<PiStatusData | null>(null)
const audit = ref<AuditRow[]>([])

const reportLoading = ref(false)
const reportTitle = ref('数字营销转化分析报告')
const report = ref<ReportData | null>(null)

const sessionId = ref('')
const sessionData = ref<Record<string, unknown> | null>(null)
const sessionError = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    const [p, a] = await Promise.all([fetchPiStatus(), fetchAuditRecent(50)])
    pi.value = p.data
    audit.value = a.data.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
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
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="Pi 编排中枢"
      description="Pi 为默认 runtime 的编排中枢：skills 生态、一键报告、审计与会话回放。stub/未安装时明确降级 local。"
    >
      <template #actions>
        <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
      </template>
    </PageHeaderBar>

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <div class="grid-2">
      <div>
        <ElCard shadow="never" class="section-card">
          <template #header>
            Runtime 状态
            <RuntimeBadge
              v-if="pi"
              :runtime="pi.installed && !pi.is_stub ? 'pi' : 'local'"
              :pi="pi"
              :fallback="Boolean(pi.is_stub || pi.fallback_reason)"
              class="ml-sm"
            />
          </template>
          <ElDescriptions v-if="pi" :column="1" size="small" border>
            <ElDescriptionsItem label="默认 runtime">
              <span class="mono">{{ pi.default_runtime }}</span>
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
            description="skills 目录：agent/skills/*/SKILL.md"
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
          <ElTable :data="audit" size="small" stripe max-height="520">
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
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: var(--space-4);
  align-items: start;
}
@media (max-width: 1100px) {
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
</style>
