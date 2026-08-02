<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { CSSProperties } from 'vue'
import type { EChartsCoreOption } from 'echarts/core'
import type { DashboardData, OverviewData } from '../api/data'
import type { HealthData } from '../api/health'
import { chartColors, COLOR_SURFACE, COLOR_TEXT } from '../utils/chartTheme'
import { formatInt, formatPercent } from '../utils/format'
import BaseChart from './BaseChart.vue'
import EmptyState from './EmptyState.vue'
import Icon from './Icon.vue'

interface QualityIssue {
  code: string
  message: string
  count: number | null
}

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
  health: HealthData | null
  issues: QualityIssue[]
}>()

const isCompact = ref(false)

function syncCompact() {
  isCompact.value = typeof window !== 'undefined' && window.matchMedia('(max-width: 720px)').matches
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
const issueTotal = computed(() => Number(props.overview.issue_count ?? 0))

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

const topChannels = computed(() => [...channels.value].sort((a, b) => b.rate - a.rate).slice(0, 4))
const maxChannelTotal = computed(() => Math.max(1, ...channels.value.map((channel) => channel.total)))
const funnelStages = computed(() => props.dashboard?.funnel ?? [])
const maxFunnelCount = computed(() => Math.max(1, ...funnelStages.value.map((stage) => Number(stage.count ?? 0))))
const splitItems = computed(() => {
  const splits = props.overview.splits ?? {}
  const items = [
    { label: 'Train', value: Number(splits.n_train ?? 0), color: 'var(--color-primary-500)' },
    { label: 'Valid', value: Number(splits.n_valid ?? 0), color: 'var(--color-secondary-500)' },
    { label: 'Test', value: Number(splits.n_test ?? 0), color: 'var(--color-warning)' },
  ]
  const total = items.reduce((sum, item) => sum + item.value, 0) || 1
  return items.map((item) => ({ ...item, pct: item.value / total }))
})

const hasSankey = computed(() => channels.value.length > 0)

const ringStyle = computed<CSSProperties>(() => ({
  '--ring-value': `${Math.min(360, Math.max(0, positiveRate.value * 360))}deg`,
}))

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
  <section class="screen-sankey" aria-label="总览大屏桑基转化总览">
    <div class="flow-title">
      <div>
        <p class="eyebrow">Screen Flow</p>
        <h2>渠道转化桑基大屏</h2>
        <p>中心展示全量样本到渠道与转化结果的流向，周围小图承接质量、阶段、划分和默认产物。</p>
      </div>
      <div class="flow-pill">
        <Icon icon="uil:chart" size="md" />
        <span>按后端统计生成</span>
      </div>
    </div>

    <div class="orbit-shell">
      <div class="sankey-panel">
        <div class="sankey-head">
          <div>
            <span>主图</span>
            <strong>{{ formatInt(totalRows) }} 条样本</strong>
          </div>
          <small>渠道 → 转化结果</small>
        </div>
        <div v-if="hasSankey" class="sankey-chart-frame">
          <BaseChart :option="sankeyOption" :height="isCompact ? '360px' : '440px'" />
        </div>
        <EmptyState v-else title="暂无渠道流向" description="请先生成 data overview 产物。" />
        <p v-if="dashboard?.caliber" class="caliber">{{ dashboard.caliber }}</p>
      </div>

      <article class="orbit-card card-conversion">
        <div class="mini-head">
          <span class="mini-icon"><Icon icon="uil:percentage" size="sm" /></span>
          <span>转化环</span>
        </div>
        <div class="ring-row">
          <div class="mini-ring" :style="ringStyle">
            <span>{{ formatPercent(positiveRate, 1) }}</span>
          </div>
          <div>
            <strong>{{ formatInt(totalConverted) }}</strong>
            <small>Conversion=1</small>
          </div>
        </div>
      </article>

      <article class="orbit-card card-channel">
        <div class="mini-head">
          <span class="mini-icon secondary"><Icon icon="uil:signal-alt-3" size="sm" /></span>
          <span>渠道强度</span>
        </div>
        <div class="bar-list">
          <div v-for="channel in topChannels" :key="channel.name" class="bar-row">
            <span>{{ channel.name }}</span>
            <div class="bar-track">
              <i :style="{ width: `${Math.max(6, channel.total / maxChannelTotal * 100)}%` }" />
            </div>
            <b>{{ formatPercent(channel.rate, 1) }}</b>
          </div>
        </div>
      </article>

      <article class="orbit-card card-funnel">
        <div class="mini-head">
          <span class="mini-icon info"><Icon icon="uil:filter" size="sm" /></span>
          <span>横截面阶段</span>
        </div>
        <div class="funnel-bars">
          <div v-for="stage in funnelStages" :key="stage.stage" class="funnel-row">
            <span>{{ stage.label }}</span>
            <div class="funnel-track">
              <i :style="{ width: `${Math.max(5, Number(stage.count ?? 0) / maxFunnelCount * 100)}%` }" />
            </div>
          </div>
        </div>
      </article>

      <article class="orbit-card card-quality">
        <div class="mini-head">
          <span class="mini-icon warning"><Icon icon="uil:shield-exclamation" size="sm" /></span>
          <span>质量告警</span>
        </div>
        <div class="quality-meter">
          <strong>{{ formatInt(issueTotal) }}</strong>
          <small>审计命中</small>
        </div>
        <p>{{ issues[0]?.message || '当前质量审计未返回明显问题。' }}</p>
      </article>

      <article class="orbit-card card-split">
        <div class="mini-head">
          <span class="mini-icon success"><Icon icon="uil:layers-alt" size="sm" /></span>
          <span>训练划分</span>
        </div>
        <div class="split-strip">
          <i
            v-for="item in splitItems"
            :key="item.label"
            :style="{ width: `${Math.max(4, item.pct * 100)}%`, background: item.color }"
          />
        </div>
        <div class="split-list">
          <span v-for="item in splitItems" :key="item.label">{{ item.label }} {{ formatInt(item.value) }}</span>
        </div>
      </article>

      <article class="orbit-card card-runtime">
        <div class="mini-head">
          <span class="mini-icon primary"><Icon icon="uil:processor" size="sm" /></span>
          <span>默认产物</span>
        </div>
        <strong class="run-id">{{ health?.default_run_id || '—' }}</strong>
        <small>{{ health?.artifacts_ok ? '模型产物就绪' : '模型产物待生成' }}</small>
      </article>
    </div>
  </section>
</template>

<style scoped>
.screen-sankey {
  min-width: 0;
  width: 100%;
}

.flow-title {
  display: flex;
  min-width: 0;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.flow-title > div {
  min-width: 0;
}

.flow-title h2 {
  margin: var(--space-1) 0;
  color: var(--text-title);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0;
}

.flow-title p {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  overflow-wrap: anywhere;
}

.eyebrow {
  color: var(--color-primary-600) !important;
  font-size: var(--font-size-xs) !important;
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
}

.flow-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-width: fit-content;
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  background: var(--bg-card);
  color: var(--text-body);
  font-size: var(--font-size-sm);
  box-shadow: var(--shadow-sm);
}

.orbit-shell {
  display: grid;
  min-width: 0;
  max-width: 100%;
  grid-template-columns: minmax(220px, 248px) minmax(0, 1fr) minmax(220px, 260px);
  gap: var(--space-5) var(--space-4);
  align-items: center;
}

.sankey-panel,
.orbit-card {
  border: 1px solid var(--border-default);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.sankey-panel {
  z-index: 2;
  grid-column: 2;
  grid-row: 1 / 4;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  border-radius: var(--radius-panel);
  padding: var(--space-5);
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

.orbit-card {
  z-index: 3;
  min-width: 0;
  max-width: 100%;
  min-height: 138px;
  overflow: hidden;
  border-radius: var(--radius-card);
  padding: var(--space-4);
}

.card-conversion { grid-column: 1; grid-row: 1; }
.card-funnel { grid-column: 1; grid-row: 2; }
.card-split { grid-column: 1; grid-row: 3; }
.card-channel { grid-column: 3; grid-row: 1; }
.card-quality { grid-column: 3; grid-row: 2; }
.card-runtime { grid-column: 3; grid-row: 3; }

.mini-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  color: var(--text-title);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.mini-icon {
  display: grid;
  width: var(--space-8);
  height: var(--space-8);
  place-items: center;
  border-radius: var(--radius-lg);
  background: var(--color-primary-50);
  color: var(--color-primary-600);
}

.mini-icon.secondary { background: var(--color-secondary-50); color: var(--color-secondary-600); }
.mini-icon.info { background: var(--color-info-bg); color: var(--color-info-text); }
.mini-icon.warning { background: var(--color-warning-bg); color: var(--color-warning-text); }
.mini-icon.success { background: var(--color-success-bg); color: var(--color-success-text); }
.mini-icon.primary { background: var(--color-primary-50); color: var(--color-primary-600); }

.ring-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.mini-ring {
  display: grid;
  width: 82px;
  height: 82px;
  place-items: center;
  border-radius: var(--radius-full);
  background: conic-gradient(var(--color-primary-500) var(--ring-value), var(--bg-tile) 0);
}

.mini-ring::before {
  grid-area: 1 / 1;
  width: 58px;
  height: 58px;
  content: '';
  border-radius: var(--radius-full);
  background: var(--bg-card);
}

.mini-ring span {
  z-index: 1;
  grid-area: 1 / 1;
  color: var(--text-title);
  font-family: var(--font-family-number);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.ring-row strong,
.quality-meter strong,
.run-id {
  display: block;
  color: var(--text-title);
  font-family: var(--font-family-number);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}

.ring-row small,
.quality-meter small,
.card-runtime small {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

.bar-list,
.funnel-bars,
.split-list {
  display: grid;
  gap: var(--space-2);
}

.bar-row {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 48px;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

.bar-row > span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-row b {
  color: var(--text-title);
  font-family: var(--font-family-number);
  font-weight: var(--font-weight-semibold);
  text-align: right;
}

.bar-track,
.funnel-track,
.split-strip {
  overflow: hidden;
  border-radius: var(--radius-full);
  background: var(--bg-tile);
}

.bar-track,
.funnel-track {
  height: 8px;
}

.bar-track i,
.funnel-track i,
.split-strip i {
  display: block;
  height: 100%;
  border-radius: var(--radius-full);
}

.bar-track i { background: var(--color-primary-500); }
.funnel-track i { background: var(--color-info); }

.funnel-row {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

.quality-meter {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.card-quality p {
  margin: var(--space-2) 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.split-strip {
  display: flex;
  height: 12px;
}

.split-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: var(--space-3);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

@media (max-width: 1180px) {
  .orbit-shell {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-4);
  }

  .orbit-card {
    width: auto;
    grid-column: auto;
    grid-row: auto;
  }

  .sankey-panel {
    grid-column: 1 / -1;
    grid-row: auto;
  }
}

@media (max-width: 720px) {
  .flow-title {
    align-items: flex-start;
    flex-direction: column;
  }

  .flow-title > div {
    width: 100%;
  }

  .flow-pill {
    width: 100%;
    justify-content: center;
  }

  .orbit-shell {
    grid-template-columns: 1fr;
  }

  .sankey-panel {
    padding: var(--space-4);
    border-radius: var(--radius-card);
  }

  .sankey-head {
    flex-direction: column;
  }

  .sankey-chart-frame {
    width: calc(100% - var(--space-6));
  }

  .orbit-card {
    min-height: auto;
  }

  .run-id {
    overflow-wrap: anywhere;
  }

  .split-list {
    grid-template-columns: 1fr;
  }
}
</style>
