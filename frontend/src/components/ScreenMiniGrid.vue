<script setup lang="ts">
/**
 * /screen 底部 2×2 小图网格（Data Dense 高密度）：渠道强度、横截面阶段、训练划分、质量与默认产物。
 * 由原 ScreenSankeyOrbit 的 orbit 徽章体系迁出，条轨高 6–8px、方角，禁止渐变/圆环/悬浮徽章。
 */
import { computed } from 'vue'
import type { DashboardData, OverviewData } from '../api/data'
import type { HealthData } from '../api/health'
import { formatInt, formatPercent } from '../utils/format'

interface QualityIssue {
  code: string
  message: string
  count: number | null
}

interface ChannelFlow {
  name: string
  total: number
  rate: number
}

const props = defineProps<{
  overview: OverviewData
  dashboard: DashboardData | null
  health: HealthData | null
  issues: QualityIssue[]
}>()

const channels = computed<ChannelFlow[]>(() =>
  (props.overview.channel_stats ?? [])
    .map((channel) => {
      const total = Math.max(0, Math.round(Number(channel.n ?? 0)))
      const rate = Math.max(0, Math.min(1, Number(channel.conversion_rate ?? 0)))
      return { name: String(channel.channel || '未标注渠道'), total, rate }
    })
    .filter((channel) => channel.total > 0),
)

const topChannels = computed(() => [...channels.value].sort((a, b) => b.rate - a.rate).slice(0, 4))
const maxChannelTotal = computed(() => Math.max(1, ...channels.value.map((channel) => channel.total)))
const funnelStages = computed(() => props.dashboard?.funnel ?? [])
const maxFunnelCount = computed(() => Math.max(1, ...funnelStages.value.map((stage) => Number(stage.count ?? 0))))
const issueTotal = computed(() => Number(props.overview.issue_count ?? 0))

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
</script>

<template>
  <div class="mini-grid">
    <article class="mini-panel">
      <h4>渠道强度</h4>
      <div class="bar-list">
        <div v-for="channel in topChannels" :key="channel.name" class="bar-row">
          <span>{{ channel.name }}</span>
          <div class="bar-track"><i :style="{ width: `${Math.max(6, channel.total / maxChannelTotal * 100)}%` }" /></div>
          <b>{{ formatPercent(channel.rate, 1) }}</b>
        </div>
      </div>
    </article>

    <article class="mini-panel">
      <h4>横截面阶段</h4>
      <div class="funnel-bars">
        <div v-for="stage in funnelStages" :key="stage.stage" class="funnel-row">
          <span>{{ stage.label }}</span>
          <div class="funnel-track"><i :style="{ width: `${Math.max(5, Number(stage.count ?? 0) / maxFunnelCount * 100)}%` }" /></div>
        </div>
      </div>
    </article>

    <article class="mini-panel">
      <h4>训练划分</h4>
      <div class="split-strip">
        <i v-for="item in splitItems" :key="item.label" :style="{ width: `${Math.max(4, item.pct * 100)}%`, background: item.color }" />
      </div>
      <div class="split-list">
        <span v-for="item in splitItems" :key="item.label">{{ item.label }} {{ formatInt(item.value) }}</span>
      </div>
    </article>

    <article class="mini-panel">
      <h4>质量与产物</h4>
      <div class="qa-line">
        <strong>{{ formatInt(issueTotal) }}</strong>
        <span>审计命中</span>
        <p>{{ issues[0]?.message || '当前质量审计未返回明显问题。' }}</p>
      </div>
      <div class="run-line">
        <span>默认 run</span>
        <strong class="run-id">{{ health?.default_run_id || '—' }}</strong>
        <small>{{ health?.artifacts_ok ? '模型产物就绪' : '模型产物待生成' }}</small>
      </div>
    </article>
  </div>
</template>

<style scoped>
.mini-grid {
  display: grid;
  min-width: 0;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}

.mini-panel {
  min-width: 0;
  padding: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-card);
  background: var(--bg-card);
  box-shadow: var(--shadow-xs);
}

.mini-panel h4 {
  margin: 0 0 var(--space-2);
  color: var(--text-title);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
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
  border-radius: var(--radius-sm);
  background: var(--bg-tile);
}

.bar-track,
.funnel-track {
  height: 6px;
}

.bar-track i,
.funnel-track i,
.split-strip i {
  display: block;
  height: 100%;
  border-radius: var(--radius-sm);
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

.split-strip {
  display: flex;
  height: 8px;
}

.split-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

.qa-line {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: baseline;
  gap: var(--space-2);
}

.qa-line strong,
.run-line .run-id {
  color: var(--text-title);
  font-family: var(--font-family-number);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.qa-line span,
.run-line span,
.run-line small {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

.qa-line p {
  grid-column: 1 / -1;
  margin: var(--space-1) 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.run-line {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.run-id {
  overflow-wrap: anywhere;
}

@media (max-width: 992px) {
  .mini-grid {
    grid-template-columns: 1fr;
  }
}
</style>
