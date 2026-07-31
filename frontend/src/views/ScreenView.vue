<script setup lang="ts">
/**
 * /screen 总览大屏（Stage 3）：数据分析 → 数据挖掘 由浅入深的开场全景。
 * 红线：所有数字来自 /api/v1；任一板块失败仅该板块降级提示，不造假数；
 * 伪漏斗为横截面独立计数（caliber 由后端产出，页脚原样展示）；时序不可做。
 */
import { computed, onMounted, ref } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import { fetchHealth, type HealthData } from '../api/health'
import {
  fetchDashboard, fetchOverview, fetchCrossMatrix,
  type DashboardData, type OverviewData, type CrossMatrixData,
} from '../api/data'
import { fetchMetrics, type MetricsListData, type MetricRow } from '../api/models'
import { fetchGlobalExplain, type GlobalExplainData } from '../api/explain'
import { chartColors, axisTheme } from '../utils/chartTheme'
import '../styles/screen.css'

const palette = chartColors('screen')
const axis = axisTheme('screen')

const health = ref<HealthData | null>(null)
const dashboard = ref<DashboardData | null>(null)
const overview = ref<OverviewData | null>(null)
const cross = ref<CrossMatrixData | null>(null)
const metrics = ref<MetricsListData | null>(null)
const shap = ref<GlobalExplainData | null>(null)
const fails = ref<Record<string, string>>({})

const fmtInt = (v?: number | null) => (v == null ? '—' : Math.round(v).toLocaleString('zh-CN'))
const pct2 = (v?: number | null) => (v == null ? '—' : `${(v * 100).toFixed(2)}%`)
const money = (v?: number | null) => (v == null ? '—' : `¥${Math.round(v).toLocaleString('zh-CN')}`)
const f2 = (v?: number | null) => (v == null ? '—' : Number(v).toFixed(2))
const f4 = (v?: number | null) => (v == null ? '—' : Number(v).toFixed(4))

const statusColor = computed(() => {
  if (!health.value) return 'var(--color-info)'
  if (health.value.status === 'ok') return 'var(--screen-chart-2)'
  if (health.value.status === 'degraded') return 'var(--screen-chart-3)'
  return 'var(--screen-chart-4)'
})

async function loadAll() {
  const tasks: Array<[string, Promise<unknown>]> = [
    ['health', fetchHealth().then((r) => (health.value = r.data))],
    ['dashboard', fetchDashboard().then((r) => (dashboard.value = r.data))],
    ['overview', fetchOverview().then((r) => (overview.value = r.data))],
    ['cross', fetchCrossMatrix().then((r) => (cross.value = r.data))],
    ['metrics', fetchMetrics().then((r) => (metrics.value = r.data))],
    ['shap', fetchGlobalExplain().then((r) => (shap.value = r.data))],
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

// ---- 图表 options（screen 主题，色板来自 chartTheme）----

const funnelOption = computed(() => {
  const f = dashboard.value?.funnel ?? []
  return {
    grid: { left: 46, right: 12, top: 24, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      formatter: (ps: Array<{ dataIndex: number }>) => {
        const s = f[ps[0].dataIndex]
        return s ? `${s.label}<br/>计数 ${fmtInt(s.count)}（占全量 ${pct2(s.rate_vs_total)}）` : ''
      },
    },
    xAxis: {
      type: 'category',
      data: f.map((s) => s.label),
      axisLabel: { color: axis.axisLabel, fontSize: 11 },
      axisLine: { lineStyle: { color: axis.splitLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: axis.axisLabel, fontSize: 10 },
      splitLine: { lineStyle: { color: axis.splitLine } },
    },
    series: [
      {
        type: 'bar',
        data: f.map((s, i) => ({ value: s.count, itemStyle: { color: palette[i % palette.length], borderRadius: [4, 4, 0, 0] } })),
        barMaxWidth: 42,
        label: {
          show: true, position: 'top', color: axis.textStyle, fontSize: 10,
          formatter: (p: { dataIndex: number }) => pct2(f[p.dataIndex]?.rate_vs_total),
        },
      },
    ],
  }
})

const channelOption = computed(() => {
  const stats = overview.value?.channel_stats ?? []
  return {
    grid: { left: 44, right: 12, top: 24, bottom: 24 },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${Number(v).toFixed(2)}%` },
    xAxis: {
      type: 'category',
      data: stats.map((c) => String(c.channel ?? '—')),
      axisLabel: { color: axis.axisLabel, fontSize: 11 },
      axisLine: { lineStyle: { color: axis.splitLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: axis.axisLabel, fontSize: 10 },
      splitLine: { lineStyle: { color: axis.splitLine } },
    },
    series: [
      {
        type: 'bar',
        data: stats.map((c) => Number((c.conversion_rate ?? 0) * 100)),
        itemStyle: { color: palette[1], borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 36,
      },
    ],
  }
})

const crossOption = computed(() => {
  const c = cross.value
  if (!c) return {}
  const rows = c.row_totals.map((t) => t.key)
  const cols = c.col_totals.map((t) => t.key)
  const data = c.cells.map((cell) => [cols.indexOf(cell.col), rows.indexOf(cell.row), cell.conversion_rate])
  const crs = c.cells.map((cell) => cell.conversion_rate)
  return {
    grid: { left: 74, right: 12, top: 10, bottom: 52 },
    tooltip: {
      position: 'top',
      formatter: (p: { data: [number, number, number] }) =>
        `${rows[p.data[1]]} × ${cols[p.data[0]]}<br/>转化率 ${(p.data[2] * 100).toFixed(2)}%`,
    },
    xAxis: {
      type: 'category', data: cols, position: 'bottom',
      axisLabel: { color: axis.axisLabel, fontSize: 10, interval: 0 },
      axisLine: { lineStyle: { color: axis.splitLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category', data: rows,
      axisLabel: { color: axis.axisLabel, fontSize: 10 },
      axisLine: { lineStyle: { color: axis.splitLine } },
      axisTick: { show: false },
    },
    visualMap: {
      min: Math.min(...crs, 0), max: Math.max(...crs, 1),
      calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 10, itemHeight: 60,
      inRange: { color: ['#0c1f3d', palette[0], palette[2]] },
      textStyle: { color: axis.axisLabel, fontSize: 9 },
      formatter: (v: number) => `${(Number(v) * 100).toFixed(0)}%`,
    },
    series: [
      {
        type: 'heatmap', data,
        label: { show: true, color: '#eaf3ff', fontSize: 10, formatter: (p: { data: [number, number, number] }) => `${(p.data[2] * 100).toFixed(0)}%` },
        itemStyle: { borderColor: 'rgba(8,20,40,0.85)', borderWidth: 2 },
        emphasis: { itemStyle: { borderColor: palette[0] } },
      },
    ],
  }
})

function histOption(key: string) {
  return computed(() => {
    const bins = dashboard.value?.histograms?.[key] ?? []
    return {
      grid: { left: 40, right: 10, top: 14, bottom: 26 },
      tooltip: {
        trigger: 'axis',
        formatter: (ps: Array<{ dataIndex: number; data: number }>) => {
          const b = bins[ps[0].dataIndex]
          return b ? `[${b.lo}, ${b.hi}]<br/>计数 ${fmtInt(ps[0].data)}` : ''
        },
      },
      xAxis: {
        type: 'category',
        data: bins.map((b) => `${b.lo % 1 === 0 ? b.lo : b.lo.toFixed(1)}`),
        axisLabel: { color: axis.axisLabel, fontSize: 9, interval: 1 },
        axisLine: { lineStyle: { color: axis.splitLine } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: axis.axisLabel, fontSize: 9 },
        splitLine: { lineStyle: { color: axis.splitLine } },
      },
      series: [
        {
          type: 'bar',
          data: bins.map((b) => b.count),
          itemStyle: { color: palette[4], borderRadius: [3, 3, 0, 0] },
        },
      ],
    }
  })
}
const ageHist = histOption('age')
const incomeHist = histOption('income')
const spendHist = histOption('ad_spend')

const shapOption = computed(() => {
  const rows = [...(shap.value?.top_features ?? [])]
    .slice(0, 8)
    .reverse()
  return {
    grid: { left: 110, right: 30, top: 8, bottom: 16 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v: number) => Number(v).toFixed(4) },
    xAxis: {
      type: 'value',
      axisLabel: { color: axis.axisLabel, fontSize: 9 },
      splitLine: { lineStyle: { color: axis.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.name),
      axisLabel: { color: axis.textStyle, fontSize: 10, width: 100, overflow: 'truncate' },
      axisLine: { lineStyle: { color: axis.splitLine } },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => r.mean_abs_shap ?? 0),
        itemStyle: { color: palette[0], borderRadius: [0, 3, 3, 0] },
        barMaxWidth: 14,
        label: { show: true, position: 'right', color: axis.textStyle, fontSize: 9, formatter: (p: { data: number }) => Number(p.data).toFixed(3) },
      },
    ],
  }
})

const leaderboard = computed(() => (metrics.value?.items ?? []).slice(0, 9))
const defaultRun = computed(() => (metrics.value as unknown as { default_run_id?: string })?.default_run_id)
const isDummy = (r: MetricRow) => String(r.exp_id ?? '').toUpperCase() === 'E0'
const isAblation = (r: MetricRow) => Boolean(r.ablation || r.includes_conversion_rate)
</script>

<template>
  <div class="screen" data-theme="screen">
    <header class="screen-header">
      <div>
        <h1 class="screen-title">数字营销转化分析 · 总览大屏</h1>
        <p class="screen-sub">数据分析 → 数据挖掘：描述 · 预测 · 分群 · 规则 · 决策模拟</p>
      </div>
      <div class="screen-status">
        <span class="screen-badge">横截面口径 · 无时序</span>
        <span>
          <span class="screen-dot" :style="{ color: statusColor, background: statusColor }" />
          {{ health ? (health.status === 'ok' ? 'API 健康' : 'API 降级') : '检查中…' }}
        </span>
        <span v-if="health?.default_run_id" class="mono">{{ health.default_run_id }}</span>
        <router-link class="screen-back" to="/">返回工作台</router-link>
      </div>
    </header>

    <div class="screen-grid">
      <!-- R1：KPI 磁贴 -->
      <section class="kpi-tiles span-12">
        <div v-for="(t, i) in [
          { label: '样本量', value: fmtInt(dashboard?.kpis.n_rows), hint: 'campaigns 全表' },
          { label: '正类占比', value: pct2(dashboard?.kpis.positive_rate), hint: 'Conversion=1' },
          { label: '总广告支出', value: money(dashboard?.kpis.total_ad_spend), hint: 'AdSpend 合计' },
          { label: '平均点击率', value: pct2(dashboard?.kpis.avg_ctr), hint: 'ClickThroughRate 均值' },
          { label: '平均访问深度', value: f2(dashboard?.kpis.avg_pages_per_visit), hint: 'PagesPerVisit 均值' },
          { label: '复购客户占比', value: pct2(dashboard?.kpis.repurchase_rate), hint: 'PreviousPurchases>0' },
        ]" :key="i" class="kpi-tile" :style="{ animationDelay: `${i * 40}ms` }">
          <div class="kpi-tile-label">{{ t.label }}</div>
          <div class="kpi-tile-value">{{ t.value }}</div>
          <div class="kpi-tile-hint">{{ t.hint }}</div>
        </div>
      </section>

      <!-- R2：伪漏斗 | 渠道转化 | 渠道×类型交叉 -->
      <section class="screen-panel span-4">
        <h2 class="screen-panel-title">行为伪漏斗 <span class="hint">横截面独立计数，非 cohort</span></h2>
        <BaseChart v-if="dashboard" :option="funnelOption" theme="screen" height="230px" />
        <div v-else class="screen-empty">{{ fails.dashboard || '加载中…' }}</div>
      </section>
      <section class="screen-panel span-4">
        <h2 class="screen-panel-title">渠道转化率 <span class="hint">/data/overview</span></h2>
        <BaseChart v-if="overview" :option="channelOption" theme="screen" height="230px" />
        <div v-else class="screen-empty">{{ fails.overview || '加载中…' }}</div>
      </section>
      <section class="screen-panel span-4">
        <h2 class="screen-panel-title">渠道 × 活动类型 <span class="hint">转化率热力</span></h2>
        <BaseChart v-if="cross" :option="crossOption" theme="screen" height="230px" />
        <div v-else class="screen-empty">{{ fails.cross || '加载中…' }}</div>
      </section>

      <!-- R3：分布直方图 -->
      <section class="screen-panel span-4">
        <h2 class="screen-panel-title">年龄分布</h2>
        <BaseChart v-if="dashboard" :option="ageHist" theme="screen" height="190px" />
        <div v-else class="screen-empty">{{ fails.dashboard || '加载中…' }}</div>
      </section>
      <section class="screen-panel span-4">
        <h2 class="screen-panel-title">收入分布</h2>
        <BaseChart v-if="dashboard" :option="incomeHist" theme="screen" height="190px" />
        <div v-else class="screen-empty">{{ fails.dashboard || '加载中…' }}</div>
      </section>
      <section class="screen-panel span-4">
        <h2 class="screen-panel-title">广告支出分布</h2>
        <BaseChart v-if="dashboard" :option="spendHist" theme="screen" height="190px" />
        <div v-else class="screen-empty">{{ fails.dashboard || '加载中…' }}</div>
      </section>

      <!-- R4：实验矩阵 mini | 全局 SHAP -->
      <section class="screen-panel span-7">
        <h2 class="screen-panel-title">实验矩阵 E0–E8 <span class="hint">主指标 PR-AUC · Accuracy 仅对照</span></h2>
        <table v-if="metrics" class="lb-table">
          <thead>
            <tr><th>实验</th><th>模型</th><th>PR-AUC</th><th>ROC-AUC</th><th>Accuracy（对照）</th></tr>
          </thead>
          <tbody>
            <tr
              v-for="r in leaderboard"
              :key="r.run_id"
              :class="{ 'is-default': r.run_id === defaultRun, 'is-dummy': isDummy(r) }"
            >
              <td>
                {{ r.exp_id ?? r.run_id }}
                <span v-if="isDummy(r)" class="lb-tag">Dummy</span>
                <span v-else-if="isAblation(r)" class="lb-tag">消融</span>
                <span v-else-if="r.run_id === defaultRun" class="lb-tag">默认</span>
              </td>
              <td>{{ r.model_name ?? '—' }}</td>
              <td>{{ f4(r.pr_auc) }}</td>
              <td>{{ f4(r.roc_auc) }}</td>
              <td>{{ f4(r.accuracy) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="screen-empty">{{ fails.metrics || '加载中…' }}</div>
      </section>
      <section class="screen-panel span-5">
        <h2 class="screen-panel-title">全局特征解释 Top8 <span class="hint">mean |SHAP|</span></h2>
        <BaseChart v-if="shap" :option="shapOption" theme="screen" height="230px" />
        <div v-else class="screen-empty">{{ fails.shap || '加载中…' }}</div>
      </section>
    </div>

    <footer class="screen-footer">
      <div v-if="dashboard?.caliber">{{ dashboard.caliber }}</div>
      <div>以下洞察基于历史数据中的相关关系与模型估计，不构成因果证明，也不构成实际投放收益承诺。</div>
    </footer>
  </div>
</template>
