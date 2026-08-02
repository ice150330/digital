<script setup lang="ts">
/**
 * /screen Halo 总览大屏：工作台框架内的渠道转化桑基图。
 * 红线：所有数字来自 /api/v1；单接口失败只降级对应节点或徽章，不造假数。
 */
import { computed, onMounted, ref } from 'vue'
import Icon from '../components/Icon.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import ScreenSankeyOrbit from '../components/ScreenSankeyOrbit.vue'
import Tag from '../components/Tag.vue'
import { fetchHealth, type HealthData } from '../api/health'
import {
  fetchDashboard,
  fetchOverview,
  fetchCrossMatrix,
  type DashboardData,
  type OverviewData,
  type CrossMatrixData,
} from '../api/data'
import { fetchMetrics, type MetricsListData } from '../api/models'
import { fetchGlobalExplain, type GlobalExplainData } from '../api/explain'
import { fetchSegments, type SegmentsData } from '../api/segments'
import { fetchRules, type RulesData } from '../api/rules'
import { simulateBudget, type BudgetSimulateData } from '../api/simulate'
import { fetchPiStatus, type PiStatusData } from '../api/agent'
import '../styles/screen.css'

type BadgeTone = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'

const health = ref<HealthData | null>(null)
const dashboard = ref<DashboardData | null>(null)
const overview = ref<OverviewData | null>(null)
const cross = ref<CrossMatrixData | null>(null)
const metrics = ref<MetricsListData | null>(null)
const shap = ref<GlobalExplainData | null>(null)
const segments = ref<SegmentsData | null>(null)
const rules = ref<RulesData | null>(null)
const budget = ref<BudgetSimulateData | null>(null)
const piStatus = ref<PiStatusData | null>(null)
const fails = ref<Record<string, string>>({})

const pct2 = (v?: number | null) => (v == null ? '—' : `${(v * 100).toFixed(2)}%`)
const money = (v?: number | null) => (v == null ? '—' : `¥${Math.round(v).toLocaleString('zh-CN')}`)
const f2 = (v?: number | null) => (v == null ? '—' : Number(v).toFixed(2))
const f4 = (v?: number | null) => (v == null ? '—' : Number(v).toFixed(4))

async function loadAll() {
  const tasks: Array<[string, Promise<unknown>]> = [
    ['health', fetchHealth().then((r) => (health.value = r.data))],
    ['dashboard', fetchDashboard().then((r) => (dashboard.value = r.data))],
    ['overview', fetchOverview().then((r) => (overview.value = r.data))],
    ['cross', fetchCrossMatrix().then((r) => (cross.value = r.data))],
    ['metrics', fetchMetrics().then((r) => (metrics.value = r.data))],
    ['shap', fetchGlobalExplain().then((r) => (shap.value = r.data))],
    ['segments', fetchSegments().then((r) => (segments.value = r.data))],
    ['rules', fetchRules(1.0, 20).then((r) => (rules.value = r.data))],
    ['budget', simulateBudget({ n_points: 12 }).then((r) => (budget.value = r.data))],
    ['pi', fetchPiStatus().then((r) => (piStatus.value = r.data))],
  ]
  await Promise.all(
    tasks.map(async ([key, p]) => {
      try {
        await p
      } catch (e) {
        fails.value[key] = e instanceof Error ? e.message : '加载失败'
      }
    }),
  )
}

onMounted(loadAll)

const leaderboard = computed(() => metrics.value?.items ?? [])
const defaultRunId = computed(() => health.value?.default_run_id ?? (metrics.value as unknown as { default_run_id?: string })?.default_run_id ?? null)
const defaultMetric = computed(() => {
  const id = defaultRunId.value
  return leaderboard.value.find((r) => r.run_id === id) ?? leaderboard.value.find((r) => String(r.exp_id ?? '').toUpperCase() !== 'E0') ?? leaderboard.value[0]
})
const topChannel = computed(() => {
  const rows = [...(overview.value?.channel_stats ?? [])]
  return rows.sort((a, b) => Number(b.conversion_rate ?? 0) - Number(a.conversion_rate ?? 0))[0]
})
const topFeature = computed(() => shap.value?.top_features?.[0])
const screenIssues = computed(() => (overview.value?.issues ?? []).map((issue) => ({
  code: String(issue.code || 'QUALITY_ISSUE'),
  message: String(issue.message || '检测到数据质量问题'),
  count: Number.isFinite(Number(issue.count)) ? Number(issue.count) : null,
})))

const statusTone = computed<BadgeTone>(() => {
  if (!health.value) return 'info'
  if (health.value.status === 'ok') return 'success'
  if (health.value.status === 'degraded') return 'warning'
  return 'danger'
})

const metricStrip = computed(() => [
  { label: '总广告支出', value: money(dashboard.value?.kpis.total_ad_spend), hint: 'AdSpend 合计' },
  { label: '平均点击率', value: pct2(dashboard.value?.kpis.avg_ctr), hint: 'ClickThroughRate' },
  { label: '访问深度', value: f2(dashboard.value?.kpis.avg_pages_per_visit), hint: 'PagesPerVisit 均值' },
  { label: '复购占比', value: pct2(dashboard.value?.kpis.repurchase_rate), hint: 'PreviousPurchases>0' },
])

const insightItems = computed(() => [
  `默认模型 ${defaultRunId.value ?? '—'} 的 PR-AUC 为 ${f4(defaultMetric.value?.pr_auc)}，Accuracy 仅作为对照信息。`,
  `当前强渠道为 ${topChannel.value?.channel ?? '—'}，描述性转化率 ${pct2(topChannel.value?.conversion_rate)}。`,
  `全局解释中 ${topFeature.value?.name ?? '—'} 的 mean |SHAP| 排名靠前，仅说明模型敏感性。`,
])
</script>

<template>
  <div class="screen page">
    <PageHeaderBar
      title="总览大屏 · 渠道转化桑基图"
      description="工作台内的浅色总览：中心展示全量样本、渠道与转化结果的流向，周围小图串起质量、阶段、划分和模型产物。"
    >
      <template #actions>
        <Tag :tone="statusTone">{{ health ? (health.status === 'ok' ? 'API 健康' : 'API 降级') : '检查中' }}</Tag>
        <Tag tone="neutral" metric>{{ defaultRunId ?? 'run 未加载' }}</Tag>
        <Tag tone="info">横截面口径 · 无时序</Tag>
      </template>
    </PageHeaderBar>

    <section class="screen-canvas">
      <ScreenSankeyOrbit
        v-if="overview"
        :overview="overview"
        :dashboard="dashboard"
        :health="health"
        :issues="screenIssues"
      />
      <div v-else class="screen-loading">
        <span class="status-dot" :class="`tone-${statusTone}`" />
        <span>正在加载桑基大屏数据</span>
      </div>

      <aside class="insight-rail">
        <div class="insight-card">
          <p class="eyebrow">Narrative</p>
          <h3>答辩开场三句话</h3>
          <ol>
            <li v-for="item in insightItems" :key="item">{{ item }}</li>
          </ol>
        </div>
        <div class="insight-card compact">
          <p class="eyebrow">Data Caliber</p>
          <p>{{ dashboard?.caliber || '口径加载中：大屏仅展示横截面描述、模型估计与产物指标。' }}</p>
        </div>
        <div class="insight-card warning">
          <Icon icon="uil:exclamation-triangle" size="lg" />
          <p>以下洞察基于历史数据中的相关关系与模型估计，不构成因果证明，也不构成实际投放收益承诺。</p>
        </div>
      </aside>
    </section>

    <section class="metric-strip">
      <div v-for="item in metricStrip" :key="item.label" class="metric-tile">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </div>
    </section>
  </div>
</template>
