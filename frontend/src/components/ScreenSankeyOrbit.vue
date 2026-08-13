<script setup lang="ts">
/**
 * /screen 中央桑基主图面板（Data Dense 高密度主图）。
 * 多阶段转化漏斗：全量样本 → 渠道 → 到访站点 → 深度浏览 → 转化 / 未转化。
 * 阶段计数来自 dashboard.channel_funnel（横截面独立计数，非嵌套，口径见 caliber）。
 * 图表色板索引语义锁定：chart-3(amber)=未转化、chart-6(green)=转化，禁止重排。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { EChartsCoreOption } from 'echarts/core'
import type { DashboardData, OverviewData } from '../api/data'
import { chartColors, COLOR_SURFACE, COLOR_TEXT } from '../utils/chartTheme'
import { formatInt, formatPercent } from '../utils/format'
import BaseChart from './BaseChart.vue'
import EmptyState from './EmptyState.vue'

interface FunnelChannel {
  channel: string
  n: number
  visited: number
  deep: number
  converted: number
}

const props = defineProps<{
  overview: OverviewData
  dashboard: DashboardData | null
}>()

const isCompact = ref(false)

function syncCompact() {
  isCompact.value = typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
}

onMounted(() => {
  syncCompact()
  window.addEventListener('resize', syncCompact)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncCompact)
})

function clampInt(value: unknown): number {
  const n = Math.round(Number(value ?? 0))
  return Number.isFinite(n) ? Math.max(0, n) : 0
}

const totalRows = computed(() => clampInt(props.dashboard?.kpis.n_rows ?? props.overview.n_rows))

const funnelChannels = computed<FunnelChannel[]>(() => {
  const rows = props.dashboard?.channel_funnel ?? []
  return rows
    .map((row) => ({
      channel: String(row.channel || '未标注渠道'),
      n: clampInt(row.n),
      visited: clampInt(row.visited),
      deep: clampInt(row.deep_visited),
      converted: clampInt(row.converted),
    }))
    .filter((row) => row.n > 0)
})

const hasSankey = computed(() => funnelChannels.value.length > 0)

const sankeyOption = computed<EChartsCoreOption>(() => {
  const palette = chartColors()
  const compact = isCompact.value
  const rows = funnelChannels.value
  if (!rows.length) return { series: [{ type: 'sankey', data: [], links: [] }] }

  const total = rows.reduce((sum, row) => sum + row.n, 0)
  const visitedTotal = rows.reduce((sum, row) => sum + row.visited, 0)
  const deepTotal = rows.reduce((sum, row) => sum + row.deep, 0)
  const convertedTotal = rows.reduce((sum, row) => sum + row.converted, 0)
  // 保守化：深度浏览 → 转化 取 min，浅浏览 → 转化 承接 converted 超出 deep 的少量样本（数据里为 0）
  const deepConverted = Math.min(deepTotal, convertedTotal)
  const shallowConverted = Math.max(0, convertedTotal - deepConverted)

  const channelColors = [palette[1], palette[3], palette[4], palette[6], palette[7]]

  const nodes = [
    { name: '全量样本', value: total, itemStyle: { color: palette[0] } },
    ...rows.map((row, index) => ({
      name: row.channel,
      value: row.n,
      itemStyle: { color: channelColors[index % channelColors.length] },
    })),
    { name: '到访站点', value: visitedTotal, itemStyle: { color: palette[0] } },
    { name: '未到访', value: Math.max(0, total - visitedTotal), itemStyle: { color: palette[7] } },
    { name: '深度浏览', value: deepTotal, itemStyle: { color: palette[4] } },
    { name: '浅浏览', value: Math.max(0, visitedTotal - deepTotal), itemStyle: { color: palette[7] } },
    { name: '转化', value: convertedTotal, itemStyle: { color: palette[5] } },
    { name: '未转化', value: Math.max(0, total - convertedTotal), itemStyle: { color: palette[2] } },
  ]

  const valueOf = new Map(nodes.map((node) => [node.name, node.value]))

  const links = [
    ...rows.map((row) => ({ source: '全量样本', target: row.channel, value: row.n })),
    ...rows.map((row) => ({ source: row.channel, target: '到访站点', value: row.visited })),
    ...rows.map((row) => ({ source: row.channel, target: '未到访', value: Math.max(0, row.n - row.visited) })),
    { source: '到访站点', target: '深度浏览', value: deepTotal },
    { source: '到访站点', target: '浅浏览', value: Math.max(0, visitedTotal - deepTotal) },
    { source: '深度浏览', target: '转化', value: deepConverted },
    { source: '深度浏览', target: '未转化', value: Math.max(0, deepTotal - deepConverted) },
    { source: '浅浏览', target: '转化', value: shallowConverted },
    { source: '浅浏览', target: '未转化', value: Math.max(0, visitedTotal - deepTotal - shallowConverted) },
    { source: '未到访', target: '未转化', value: Math.max(0, total - visitedTotal) },
  ].filter((link) => link.value > 0)

  return {
    color: palette,
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (params: { dataType?: string; data?: { source?: string; target?: string; name?: string; value?: number } }) => {
        const data = params.data ?? {}
        const value = formatInt(Number(data.value ?? 0))
        if (params.dataType === 'edge') {
          const sourceValue = valueOf.get(data.source ?? '') ?? 0
          const pct = sourceValue > 0 ? `（占 ${data.source} 的 ${formatPercent(Number(data.value ?? 0) / sourceValue, 1)}）` : ''
          return `${data.source} → ${data.target}<br/><b>${value}</b> 条样本${pct}`
        }
        const nodeValue = valueOf.get(data.name ?? '') ?? 0
        const share = total > 0 ? `（占全量 ${formatPercent(nodeValue / total, 1)}）` : ''
        return `<b>${data.name}</b><br/>${value} 条样本${share}`
      },
    },
    series: [
      {
        type: 'sankey',
        orient: compact ? 'vertical' : 'horizontal',
        left: compact ? 36 : 8,
        right: compact ? 52 : 80,
        top: compact ? 8 : 16,
        bottom: compact ? 8 : 18,
        nodeWidth: compact ? 14 : 18,
        nodeGap: compact ? 9 : 12,
        nodeAlign: 'justify',
        draggable: false,
        emphasis: { focus: 'adjacency' },
        label: {
          show: !compact,
          color: COLOR_TEXT,
          fontSize: 11,
          fontWeight: 600,
          formatter: (p: { name: string; value: number }) => `${p.name}\n${formatInt(p.value)}`,
        },
        lineStyle: {
          color: 'gradient',
          opacity: 0.32,
          curveness: 0.5,
        },
        itemStyle: {
          borderColor: COLOR_SURFACE,
          borderWidth: 1,
        },
        data: nodes,
        links,
      },
    ],
  }
})
</script>

<template>
  <section class="sankey-panel" aria-label="渠道转化漏斗桑基主图">
    <div class="sankey-head">
      <div>
        <span>主图</span>
        <strong>{{ formatInt(totalRows) }} 条样本</strong>
      </div>
      <small>渠道 → 到访 → 深度 → 转化</small>
    </div>
    <div v-if="hasSankey" class="sankey-chart-frame">
      <BaseChart :option="sankeyOption" :height="isCompact ? '360px' : 'var(--chart-height-hero)'" />
    </div>
    <EmptyState v-else title="暂无渠道漏斗" description="请先生成 data overview 与 dashboard 产物。" />
    <p v-if="dashboard?.caliber" class="caliber">{{ dashboard.caliber }}</p>
  </section>
</template>

<style scoped>
.sankey-panel {
  min-width: 0;
  max-width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-panel);
  background: var(--bg-card);
  box-shadow: var(--shadow-xs);
}

.sankey-head {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.sankey-head div {
  display: grid;
  gap: var(--space-1);
}

.sankey-head span,
.sankey-head small {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

.sankey-head strong {
  color: var(--text-title);
  font-family: var(--font-family-number);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
}

.sankey-chart-frame {
  min-width: 0;
  max-width: 100%;
}

.caliber {
  margin: var(--space-2) 0 0;
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  line-height: 1.6;
  overflow-wrap: anywhere;
}

@media (max-width: 640px) {
  .sankey-head {
    flex-direction: column;
  }
}
</style>
