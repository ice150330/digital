<script setup lang="ts">
/**
 * /screen Halo 总览大屏：工作台框架内的中央转化星图。
 * 红线：所有数字来自 /api/v1；单接口失败只降级对应节点或徽章，不造假数。
 */
import { computed, onMounted, ref } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import Icon from '../components/Icon.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
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
import {
  chartColors,
  COLOR_TEXT,
} from '../utils/chartTheme'
import '../styles/screen.css'

type BadgeTone = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'

interface OrbitBadge {
  key: string
  to: string
  icon: string
  label: string
  value: string
  hint: string
  tone: BadgeTone
  source: string
  failed?: boolean
}

const palette = chartColors()

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

const fmtInt = (v?: number | null) => (v == null ? '—' : Math.round(v).toLocaleString('zh-CN'))
const pct2 = (v?: number | null) => (v == null ? '—' : `${(v * 100).toFixed(2)}%`)
const money = (v?: number | null) => (v == null ? '—' : `¥${Math.round(v).toLocaleString('zh-CN')}`)
const f2 = (v?: number | null) => (v == null ? '—' : Number(v).toFixed(2))
const f4 = (v?: number | null) => (v == null ? '—' : Number(v).toFixed(4))
const short = (v?: string | null, max = 16) => {
  if (!v) return '—'
  return v.length > max ? `${v.slice(0, max)}…` : v
}

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
const topCrossCell = computed(() => {
  const rows = [...(cross.value?.cells ?? [])]
  return rows.sort((a, b) => Number(b.conversion_rate ?? 0) - Number(a.conversion_rate ?? 0))[0]
})
const topFeature = computed(() => shap.value?.top_features?.[0])
const topSegment = computed(() => {
  const rows = [...(segments.value?.clusters ?? [])]
  return rows.sort((a, b) => Number(b.share ?? 0) - Number(a.share ?? 0))[0]
})
const topRule = computed(() => rules.value?.rules?.[0])
const recommendedBudget = computed(() => budget.value?.recommended ?? null)

const statusTone = computed<BadgeTone>(() => {
  if (!health.value) return 'info'
  if (health.value.status === 'ok') return 'success'
  if (health.value.status === 'degraded') return 'warning'
  return 'danger'
})

const orbitBadges = computed<OrbitBadge[]>(() => [
  {
    key: 'data',
    to: '/',
    icon: 'uil:database',
    label: '样本量',
    value: fmtInt(dashboard.value?.kpis.n_rows ?? health.value?.campaigns_count),
    hint: 'campaigns 主数据轨',
    tone: fails.value.dashboard ? 'warning' : 'primary',
    source: '/data/dashboard',
    failed: Boolean(fails.value.dashboard),
  },
  {
    key: 'conversion',
    to: '/',
    icon: 'uil:percentage',
    label: '转化占比',
    value: pct2(dashboard.value?.kpis.positive_rate),
    hint: 'Conversion=1',
    tone: 'success',
    source: '/data/dashboard',
    failed: Boolean(fails.value.dashboard),
  },
  {
    key: 'channel',
    to: '/',
    icon: 'uil:megaphone',
    label: '强渠道',
    value: short(topChannel.value?.channel, 10),
    hint: pct2(topChannel.value?.conversion_rate),
    tone: 'info',
    source: '/data/overview',
    failed: Boolean(fails.value.overview),
  },
  {
    key: 'quality',
    to: '/',
    icon: 'uil:shield-exclamation',
    label: '质量问题',
    value: fmtInt(overview.value?.issue_count),
    hint: '保留 + flag 口径',
    tone: Number(overview.value?.issue_count ?? 0) > 0 ? 'warning' : 'success',
    source: '/data/overview',
    failed: Boolean(fails.value.overview),
  },
  {
    key: 'model',
    to: '/models',
    icon: 'uil:chart-line',
    label: 'PR-AUC',
    value: f4(defaultMetric.value?.pr_auc),
    hint: defaultRunId.value ?? '默认 run',
    tone: 'primary',
    source: '/models/metrics',
    failed: Boolean(fails.value.metrics),
  },
  {
    key: 'shap',
    to: '/models',
    icon: 'uil:atom',
    label: 'Top SHAP',
    value: short(topFeature.value?.name, 12),
    hint: f4(topFeature.value?.mean_abs_shap),
    tone: 'neutral',
    source: '/explain/global',
    failed: Boolean(fails.value.shap),
  },
  {
    key: 'segment',
    to: '/segments',
    icon: 'uil:users-alt',
    label: '主簇',
    value: topSegment.value ? `C${topSegment.value.cluster_id}` : '—',
    hint: topSegment.value ? `${pct2(topSegment.value.share)} · ${pct2(topSegment.value.conversion_rate)}` : '分群画像',
    tone: 'info',
    source: '/segments',
    failed: Boolean(fails.value.segments),
  },
  {
    key: 'rule',
    to: '/rules',
    icon: 'uil:code-branch',
    label: 'Top Lift',
    value: f2(topRule.value?.lift),
    hint: topRule.value ? short(`${topRule.value.antecedents} → ${topRule.value.consequents}`, 18) : '关联规则',
    tone: 'warning',
    source: '/rules',
    failed: Boolean(fails.value.rules),
  },
  {
    key: 'budget',
    to: '/simulate',
    icon: 'uil:wallet',
    label: '推荐触达',
    value: fmtInt(budget.value?.recommended_k),
    hint: recommendedBudget.value ? money(recommendedBudget.value.expected_net) : '期望值口径',
    tone: 'success',
    source: '/simulate/budget',
    failed: Boolean(fails.value.budget),
  },
  {
    key: 'agent',
    to: '/agent',
    icon: 'uil:comment-dots',
    label: 'Agent',
    value: piStatus.value?.default_runtime ?? '—',
    hint: piStatus.value?.bridge_ready ? 'Pi bridge ready' : (piStatus.value?.fallback_reason ?? 'runtime 状态'),
    tone: piStatus.value?.bridge_ready ? 'success' : 'neutral',
    source: '/agent/pi/status',
    failed: Boolean(fails.value.pi),
  },
])

const badgePositions = [
  ['50%', '10%'],
  ['74%', '15%'],
  ['84%', '35%'],
  ['83%', '65%'],
  ['70%', '84%'],
  ['50%', '90%'],
  ['30%', '84%'],
  ['17%', '65%'],
  ['16%', '35%'],
  ['26%', '15%'],
]

function badgeStyle(index: number) {
  const pos = badgePositions[index % badgePositions.length]
  return { left: pos[0], top: pos[1] }
}

const graphOption = computed(() => {
  const nodes: Array<Record<string, unknown>> = [
    {
      id: 'center',
      name: '转化预测中枢',
      value: defaultMetric.value?.pr_auc ?? 0,
      x: 500,
      y: 310,
      symbolSize: 122,
      category: 0,
      itemStyle: { color: palette[0], borderColor: '#ffffff', borderWidth: 8, shadowBlur: 28, shadowColor: 'rgba(87,73,244,.28)' },
      label: {
        show: true,
        formatter: `PR-AUC\n${f4(defaultMetric.value?.pr_auc)}`,
        color: '#ffffff',
        fontSize: 18,
        fontWeight: 700,
        lineHeight: 26,
      },
      tooltip: `默认 run：${defaultRunId.value ?? '—'}<br/>模型：${defaultMetric.value?.model_name ?? '—'}<br/>阈值：${f4(defaultMetric.value?.threshold)}`,
    },
  ]
  const links: Array<Record<string, unknown>> = []

  const addNode = (id: string, name: string, group: number, angle: number, size: number, color: string, tooltip: string) => {
    const rad = (angle / 180) * Math.PI
    nodes.push({
      id,
      name,
      x: 500 + Math.cos(rad) * 315,
      y: 310 + Math.sin(rad) * 205,
      symbolSize: size,
      category: group,
      itemStyle: { color, borderColor: '#ffffff', borderWidth: 4, shadowBlur: 16, shadowColor: `${color}44` },
      label: { show: true, color: COLOR_TEXT, fontSize: 12, fontWeight: 600, formatter: name },
      tooltip,
    })
    links.push({
      source: 'center',
      target: id,
      value: size,
      lineStyle: { width: Math.max(1, size / 22), color: color, opacity: 0.36, curveness: 0.08 },
    })
  }

  const channelRows = [...(overview.value?.channel_stats ?? [])]
    .sort((a, b) => Number(b.conversion_rate ?? 0) - Number(a.conversion_rate ?? 0))
    .slice(0, 4)
  channelRows.forEach((row, idx) => {
    addNode(
      `channel-${idx}`,
      short(String(row.channel ?? '渠道'), 8),
      1,
      -150 + idx * 22,
      42 + Math.min(18, Number(row.conversion_rate ?? 0) * 16),
      palette[(idx + 1) % palette.length],
      `渠道：${row.channel ?? '—'}<br/>样本：${fmtInt(row.n)}<br/>转化率：${pct2(row.conversion_rate)}`,
    )
  })

  const featureRows = [...(shap.value?.top_features ?? [])].slice(0, 4)
  featureRows.forEach((row, idx) => {
    addNode(
      `feature-${idx}`,
      short(row.name, 10),
      2,
      -28 + idx * 24,
      38 + Math.min(20, Number(row.mean_abs_shap ?? 0) * 36),
      palette[(idx + 4) % palette.length],
      `特征：${row.name}<br/>mean |SHAP|：${f4(row.mean_abs_shap)}<br/>口径：模型解释，不构成因果`,
    )
  })

  const segmentRows = [...(segments.value?.clusters ?? [])]
    .sort((a, b) => Number(b.share ?? 0) - Number(a.share ?? 0))
    .slice(0, 3)
  segmentRows.forEach((row, idx) => {
    addNode(
      `segment-${idx}`,
      `C${row.cluster_id}`,
      3,
      72 + idx * 32,
      38 + Math.min(20, Number(row.share ?? 0) * 90),
      palette[(idx + 2) % palette.length],
      `分群：C${row.cluster_id}<br/>占比：${pct2(row.share)}<br/>事后转化率：${pct2(row.conversion_rate)}`,
    )
  })

  if (topCrossCell.value) {
    addNode(
      'cross-hot',
      '交叉热点',
      4,
      158,
      58,
      palette[2],
      `${topCrossCell.value.row} × ${topCrossCell.value.col}<br/>转化率：${pct2(topCrossCell.value.conversion_rate)}<br/>样本：${fmtInt(topCrossCell.value.n)}`,
    )
  }
  if (budget.value) {
    addNode(
      'budget',
      '预算触达',
      5,
      205,
      58,
      palette[5],
      `推荐 K：${fmtInt(budget.value.recommended_k)}<br/>期望净收益：${recommendedBudget.value ? money(recommendedBudget.value.expected_net) : '—'}<br/>非因果收益承诺`,
    )
  }

  return {
    color: palette,
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (p: { dataType?: string; data?: { tooltip?: string }; name?: string }) => p.data?.tooltip ?? p.name ?? '',
    },
    series: [
      {
        type: 'graph',
        layout: 'none',
        coordinateSystem: null,
        roam: false,
        draggable: false,
        data: nodes,
        links,
        categories: [
          { name: '预测中枢' },
          { name: '渠道' },
          { name: '解释' },
          { name: '分群' },
          { name: '交叉热点' },
          { name: '预算' },
        ],
        left: 'center',
        top: 'middle',
        width: 1000,
        height: 620,
        edgeSymbol: ['none', 'circle'],
        edgeSymbolSize: [0, 5],
        lineStyle: { color: 'source', opacity: 0.28, curveness: 0.08 },
        label: { position: 'bottom' },
        emphasis: { focus: 'adjacency', lineStyle: { opacity: 0.75, width: 4 } },
      },
    ],
  }
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
      title="总览大屏 · Halo 转化星图"
      description="工作台内的浅色总览：中心展示模型、渠道、解释、分群、规则与预算模拟的关系，所有数字均来自后端接口。"
    >
      <template #actions>
        <Tag :tone="statusTone">{{ health ? (health.status === 'ok' ? 'API 健康' : 'API 降级') : '检查中' }}</Tag>
        <Tag tone="neutral" metric>{{ defaultRunId ?? 'run 未加载' }}</Tag>
        <Tag tone="info">横截面口径 · 无时序</Tag>
      </template>
    </PageHeaderBar>

    <section class="screen-canvas">
      <div class="orbit-panel">
        <div class="orbit-panel-head">
          <div>
            <p class="eyebrow">Conversion Orbit</p>
            <h2>中央转化星图</h2>
          </div>
          <div class="orbit-status">
            <span class="status-dot" :class="`tone-${statusTone}`" />
            <span>{{ health?.message || '工具接地数据加载中' }}</span>
          </div>
        </div>

        <div class="orbit-field">
          <div class="orbit-chart-shell">
            <BaseChart :option="graphOption" height="min(58vh, 620px)" />
          </div>
          <router-link
            v-for="(badge, i) in orbitBadges"
            :key="badge.key"
            :to="badge.to"
            class="orbit-badge"
            :class="[`tone-${badge.tone}`, { 'is-failed': badge.failed }]"
            :style="badgeStyle(i)"
            :title="`${badge.source} · ${badge.hint}`"
          >
            <span class="badge-icon"><Icon :icon="badge.icon" size="md" /></span>
            <span class="badge-copy">
              <span class="badge-label">{{ badge.label }}</span>
              <strong>{{ badge.failed ? '降级' : badge.value }}</strong>
              <small>{{ badge.failed ? fails[badge.key] || '接口失败' : badge.hint }}</small>
            </span>
          </router-link>
        </div>
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
