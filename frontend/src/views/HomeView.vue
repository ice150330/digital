<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElButton, ElCard } from 'element-plus'
import { fetchDashboard, fetchOverview, type DashboardData, type OverviewData } from '../api/data'
import { fetchHealth, type HealthData } from '../api/health'
import ChannelBarChart from '../components/ChannelBarChart.vue'
import ConversionDonutChart from '../components/ConversionDonutChart.vue'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import KpiCard from '../components/KpiCard.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import QualityIssueRow from '../components/QualityIssueRow.vue'
import { formatInt, formatPercent } from '../utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const overview = ref<OverviewData | null>(null)
const health = ref<HealthData | null>(null)
const dashboard = ref<DashboardData | null>(null)

const issues = computed(() => (overview.value?.issues ?? []).map((issue) => ({
  code: String(issue.code || 'QUALITY_ISSUE'),
  message: String(issue.message || '检测到数据质量问题'),
  count: Number.isFinite(Number(issue.count)) ? Number(issue.count) : null,
})))

const formatMoney = (value?: number | null) => value == null ? '—' : `¥${Math.round(value).toLocaleString('zh-CN')}`
const formatDecimal = (value?: number | null) => value == null ? '—' : Number(value).toFixed(2)

async function load() {
  loading.value = true
  error.value = null
  try {
    const [ov, h, dash] = await Promise.allSettled([fetchOverview(), fetchHealth(), fetchDashboard()])
    if (ov.status === 'rejected') throw ov.reason
    overview.value = ov.value.data
    health.value = h.status === 'fulfilled' ? h.value.data : null
    dashboard.value = dash.status === 'fulfilled' ? dash.value.data : null
  } catch (e) {
    overview.value = null
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="总览"
      description="数据规模、正类占比、渠道转化与质量告警。数字均来自后端产物。"
    >
      <template #actions>
        <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
      </template>
    </PageHeaderBar>

    <div v-if="loading" class="card-grid" aria-label="正在加载总览指标">
      <KpiCard v-for="index in 6" :key="index" label="" value="" loading />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="load" />

    <template v-else-if="overview">
      <div class="card-grid">
        <KpiCard label="样本量" :value="formatInt(dashboard?.kpis.n_rows ?? overview.n_rows)" hint="campaigns 全表" icon="uil:database" />
        <KpiCard
          label="正类占比"
          :value="formatPercent(dashboard?.kpis.positive_rate ?? overview.positive_rate)"
          hint="Conversion=1"
          icon="uil:percentage"
          tone="success"
        />
        <KpiCard
          label="总广告支出"
          :value="formatMoney(dashboard?.kpis.total_ad_spend)"
          hint="AdSpend 合计"
          icon="uil:bill"
          tone="secondary"
        />
        <KpiCard
          label="平均点击率"
          :value="formatPercent(dashboard?.kpis.avg_ctr)"
          hint="ClickThroughRate 均值"
          icon="uil:mouse-alt"
          tone="info"
        />
        <KpiCard
          label="平均访问深度"
          :value="formatDecimal(dashboard?.kpis.avg_pages_per_visit)"
          hint="PagesPerVisit 均值"
          icon="uil:layers-alt"
          tone="warning"
        />
        <KpiCard
          label="复购客户占比"
          :value="formatPercent(dashboard?.kpis.repurchase_rate)"
          hint="PreviousPurchases > 0"
          icon="uil:repeat"
          tone="primary"
        />
      </div>

      <div class="insight-grid">
        <ElCard shadow="never" class="section-card">
          <template #header>转化占比</template>
          <ConversionDonutChart
            v-if="(dashboard?.kpis.n_rows ?? overview.n_rows) && (dashboard?.kpis.positive_rate ?? overview.positive_rate) != null"
            :total="Number(dashboard?.kpis.n_rows ?? overview.n_rows)"
            :positive-rate="Number(dashboard?.kpis.positive_rate ?? overview.positive_rate)"
          />
          <EmptyState v-else title="暂无转化统计" description="请先导入 campaigns 数据。" />
        </ElCard>

        <ElCard shadow="never" class="section-card">
          <template #header>渠道转化率</template>
          <ChannelBarChart
            v-if="overview.channel_stats?.length"
            :channels="overview.channel_stats"
          />
          <EmptyState v-else title="暂无渠道统计" description="请确认 quality_profile 已生成。" />
        </ElCard>

        <ElCard shadow="never" class="section-card">
          <template #header>质量问题</template>
          <div v-if="issues.length" class="quality-list">
            <QualityIssueRow v-for="issue in issues" :key="issue.code" v-bind="issue" />
          </div>
          <EmptyState v-else title="未发现质量问题" description="当前质量审计没有返回 issue。" />
        </ElCard>
      </div>

      <ElCard shadow="never" class="section-card">
        <template #header>数据划分与模型约束</template>
        <ul class="meta-list">
          <li>Train / Valid / Test：{{ formatInt(overview.splits?.n_train) }} / {{ formatInt(overview.splits?.n_valid) }} / {{ formatInt(overview.splits?.n_test) }}</li>
          <li>质量问题总数：{{ formatInt(overview.issue_count) }}；无效 Web 指标 flag：{{ formatInt(overview.invalid_web_metrics_count) }}</li>
          <li>默认 run：<span class="mono">{{ health?.default_run_id || '—' }}</span>（{{ health?.artifacts_ok ? '产物就绪' : '产物未就绪' }}）</li>
          <li>metrics 不进 SQLite；CustomerID 永不入模；ConversionRate 默认不进入主模型。</li>
        </ul>
      </ElCard>
    </template>

    <EmptyState
      v-else-if="!loading"
      title="缺少总览产物"
      description="请运行 python scripts/01_clean_data.py 或 python scripts/run_all.py"
    />
  </div>
</template>

<style scoped>
.card-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); margin-bottom: var(--space-4); }
.insight-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.2fr) minmax(0, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}
@media (max-width: 1200px) {
  .card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .insight-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 720px) { .card-grid { grid-template-columns: 1fr; } }
.quality-list { max-height: 280px; overflow-y: auto; }
.meta-list {
  margin: 0;
  padding-left: var(--space-5);
  color: var(--text-body);
  font-size: var(--font-size-sm);
  line-height: 1.9;
}
</style>
