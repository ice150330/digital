<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElButton, ElCard, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { fetchOverview, type OverviewData } from '../api/data'
import { fetchHealth, type HealthData } from '../api/health'
import ChannelBarChart from '../components/ChannelBarChart.vue'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import KpiCard from '../components/KpiCard.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import { formatInt, formatPercent } from '../utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const overview = ref<OverviewData | null>(null)
const health = ref<HealthData | null>(null)

const issues = computed(() => overview.value?.issues ?? [])

async function load() {
  loading.value = true
  error.value = null
  try {
    const [ov, h] = await Promise.all([fetchOverview(), fetchHealth()])
    overview.value = ov.data
    health.value = h.data
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

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <template v-else-if="overview">
      <div class="card-grid">
        <KpiCard label="样本量" :value="formatInt(overview.n_rows)" hint="清洗后行数" />
        <KpiCard
          label="正类占比"
          :value="formatPercent(overview.positive_rate)"
          hint="Conversion=1"
        />
        <KpiCard
          label="质量问题"
          :value="formatInt(overview.issue_count)"
          :hint="`邮件不一致 ${formatInt(overview.email_inconsistent_count)}`"
        />
        <KpiCard
          label="默认模型"
          :value="health?.default_run_id || '—'"
          :hint="health?.artifacts_ok ? '产物就绪' : '产物未就绪'"
        />
      </div>

      <div class="two-col">
        <ElCard shadow="never" class="section-card">
          <template #header>渠道转化率</template>
          <ChannelBarChart
            v-if="overview.channel_stats?.length"
            :channels="overview.channel_stats"
          />
          <EmptyState v-else title="暂无渠道统计" description="请确认 quality_profile 已生成。" />
        </ElCard>

        <ElCard shadow="never" class="section-card">
          <template #header>划分与说明</template>
          <ul class="meta-list">
            <li>Train / Valid / Test：
              {{ formatInt(overview.splits?.n_train) }} /
              {{ formatInt(overview.splits?.n_valid) }} /
              {{ formatInt(overview.splits?.n_test) }}
            </li>
            <li>无效 Web 指标 flag：{{ formatInt(overview.invalid_web_metrics_count) }}</li>
            <li>metrics 不进 SQLite：{{ overview.notes?.metrics_not_in_sqlite ? '是' : '—' }}</li>
            <li>CustomerID 永不入模：{{ overview.notes?.customer_id_never_in_model ? '是' : '—' }}</li>
          </ul>
        </ElCard>
      </div>

      <ElCard shadow="never" class="section-card">
        <template #header>质量问题列表</template>
        <ElTable v-if="issues.length" :data="issues" size="small" stripe>
          <ElTableColumn prop="code" label="代码" width="180" />
          <ElTableColumn prop="count" label="计数" width="100" />
          <ElTableColumn prop="message" label="说明" />
          <ElTableColumn label="级别" width="100">
            <template #default>
              <ElTag type="warning" size="small">告警</ElTag>
            </template>
          </ElTableColumn>
        </ElTable>
        <EmptyState v-else title="无质量 issue" description="或尚未生成 quality_profile。" />
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
.two-col {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 992px) {
  .two-col {
    grid-template-columns: 1fr;
  }
}
.meta-list {
  margin: 0;
  padding-left: 18px;
  color: var(--color-text);
  font-size: 13px;
  line-height: 1.9;
}
</style>
