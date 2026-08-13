<script setup lang="ts">
/**
 * /screen 中央桑基主图面板（Data Dense 高密度主图）。
 * 原 orbit 徽章体系已解散迁至 ScreenMiniGrid；本组件只保留桑基渲染。
 * 桑基 option 构造与图表色板索引语义（chart-3=未转化、chart-6=转化）保持不变。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { EChartsCoreOption } from 'echarts/core'
import type { DashboardData, OverviewData } from '../api/data'
import { chartColors, COLOR_SURFACE, COLOR_TEXT } from '../utils/chartTheme'
import { formatInt } from '../utils/format'
import BaseChart from './BaseChart.vue'
import EmptyState from './EmptyState.vue'

interface ChannelFlow {
  name: string
  total: number
  positive: number
  negative: number
  rate: number
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

const totalRows = computed(() => Number(props.dashboard?.kpis.n_rows ?? props.overview.n_rows ?? 0))
const positiveRate = computed(() => Number(props.dashboard?.kpis.positive_rate ?? props.overview.positive_rate ?? 0))
const totalConverted = computed(() => Math.round(totalRows.value * positiveRate.value))

const channels = computed<ChannelFlow[]>(() =>
  (props.overview.channel_stats ?? [])
    .map((channel) => {
      const total = Math.max(0, Math.round(Number(channel.n ?? 0)))
      const rate = Math.max(0, Math.min(1, Number(channel.conversion_rate ?? 0)))
      const positive = Math.min(total, Math.round(total * rate))
      return {
        name: String(channel.channel || '未标注渠道'),
        total,
        positive,
        negative: Math.max(0, total - positive),
        rate,
      }
    })
    .filter((channel) => channel.total > 0),
)

const hasSankey = computed(() => channels.value.length > 0)

const sankeyOption = computed<EChartsCoreOption>(() => {
  const palette = chartColors()
  const compact = isCompact.value
  return {
    color: palette,
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (params: { dataType?: string; data?: { source?: string; target?: string; name?: string; value?: number } }) => {
        const data = params.data ?? {}
        const value = formatInt(Number(data.value ?? 0))
        if (params.dataType === 'edge') return `${data.source} → ${data.target}<br/>${value} 条样本`
        return `${data.name}<br/>${value} 条样本`
      },
    },
        series: [
      {
        type: 'sankey',
        orient: compact ? 'vertical' : 'horizontal',
        left: compact ? 36 : 8,
        right: compact ? 52 : 70,
        top: compact ? 8 : 16,
        bottom: compact ? 8 : 18,
        nodeWidth: compact ? 14 : 18,
        nodeGap: compact ? 9 : 13,
        nodeAlign: 'justify',
        draggable: false,
        emphasis: { focus: 'adjacency' },
        label: {
          show: !compact,
          color: COLOR_TEXT,
          fontSize: 12,
          fontWeight: 600,
        },
        lineStyle: {
          color: 'gradient',
          opacity: 0.3,
          curveness: 0.5,
        },
        itemStyle: {
          borderColor: COLOR_SURFACE,
          borderWidth: 1,
        },
        data: [
          { name: '全量样本', value: totalRows.value, itemStyle: { color: palette[0] } },
          ...channels.value.map((channel, index) => ({
            name: channel.name,
            value: channel.total,
            itemStyle: { color: palette[(index + 1) % palette.length] },
          })),
          { name: '转化', value: totalConverted.value, itemStyle: { color: palette[5] } },
          {
            name: '未转化',
            value: Math.max(0, totalRows.value - totalConverted.value),
            itemStyle: { color: palette[2] },
          },
        ],
        links: channels.value.flatMap((channel) => [
          { source: '全量样本', target: channel.name, value: channel.total },
          { source: channel.name, target: '转化', value: channel.positive },
          { source: channel.name, target: '未转化', value: channel.negative },
        ]),
      },
    ],
  }
})
</script>

<template>
  <section class="sankey-panel" aria-label="渠道转化桑基主图">
    <div class="sankey-head">
      <div>
        <span>主图</span>
        <strong>{{ formatInt(totalRows) }} 条样本</strong>
      </div>
      <small>渠道 → 转化结果</small>
    </div>
    <div v-if="hasSankey" class="sankey-chart-frame">
      <BaseChart :option="sankeyOption" :height="isCompact ? '320px' : 'var(--chart-height-hero)'" />
    </div>
    <EmptyState v-else title="暂无渠道流向" description="请先生成 data overview 产物。" />
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
