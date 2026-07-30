<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  ElButton, ElCard, ElOption, ElSelect, ElSlider, ElTable, ElTableColumn, ElTag,
} from 'element-plus'
import {
  fetchCalibration, fetchCurves, fetchLift, fetchMetric, fetchMetrics, fetchThresholdScan,
  type CalibrationData, type CurvesData, type LiftData, type MetricRow, type MetricsListData,
  type ThresholdScanData,
} from '../api/models'
import { fetchGlobalExplain, type GlobalExplainData } from '../api/explain'
import CalibrationChart from '../components/CalibrationChart.vue'
import ConfusionHeatmap from '../components/ConfusionHeatmap.vue'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LiftChart from '../components/LiftChart.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import RocPrCurveChart from '../components/RocPrCurveChart.vue'
import ShapBarChart from '../components/ShapBarChart.vue'
import ThresholdScanChart from '../components/ThresholdScanChart.vue'
import { formatMetric } from '../utils/format'

const CALIB_RUN = 'E8_lightgbm_calibrated'

const loading = ref(true)
const error = ref<string | null>(null)
const metrics = ref<MetricsListData | null>(null)
const globalExplain = ref<GlobalExplainData | null>(null)

const selectedRun = ref<string>('')
const curves = ref<CurvesData | null>(null)
const detail = ref<Record<string, unknown> | null>(null)
const lift = ref<LiftData | null>(null)
const scan = ref<ThresholdScanData | null>(null)
const calibration = ref<CalibrationData | null>(null)
const sliderThreshold = ref(0.5)

const items = computed(() => metrics.value?.items ?? [])
const bestPr = computed(() => {
  const vals = items.value
    .filter((r) => !isDummy(r) && !r.ablation)
    .map((r) => r.pr_auc)
    .filter((v): v is number => v != null)
  return vals.length ? Math.max(...vals) : null
})

const shapItems = computed(() =>
  (globalExplain.value?.top_features ?? []).map((f) => ({
    name: f.name,
    value: Number(f.mean_abs_shap ?? f.shap_value ?? 0),
  })),
)

const confusion = computed(() => {
  const c = detail.value?.confusion as { tn: number; fp: number; fn: number; tp: number } | undefined
  return c ?? null
})

const sliderRow = computed(() => {
  if (!scan.value?.rows?.length) return null
  let best = scan.value.rows[0]
  for (const r of scan.value.rows) {
    if (Math.abs(r.threshold - sliderThreshold.value) < Math.abs(best.threshold - sliderThreshold.value)) best = r
  }
  return best
})

function isDummy(row: MetricRow | Record<string, unknown>) {
  return (
    String(row.exp_id || '').toUpperCase() === 'E0' ||
    /dummy/i.test(String(row.model_name || ''))
  )
}

function isAblation(row: MetricRow | Record<string, unknown>) {
  return Boolean(row.ablation) || Boolean(row.includes_conversion_rate)
}

async function loadRunDetail(runId: string) {
  curves.value = null
  detail.value = null
  lift.value = null
  scan.value = null
  try {
    const [c, d, l, s] = await Promise.all([
      fetchCurves(runId),
      fetchMetric(runId),
      fetchLift(runId),
      fetchThresholdScan(runId),
    ])
    curves.value = c.data
    detail.value = d.data as unknown as Record<string, unknown>
    lift.value = l.data
    scan.value = s.data
    if (s.data.current_threshold != null) sliderThreshold.value = s.data.current_threshold
  } catch {
    /* 部分产物缺失时保留已加载项 */
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const m = await fetchMetrics()
    metrics.value = m.data
    const defaultRun =
      m.data.items.find((r) => !isDummy(r) && !isAblation(r) && r.run_id)?.run_id ??
      m.data.items[0]?.run_id ??
      ''
    selectedRun.value = defaultRun
    if (defaultRun) await loadRunDetail(defaultRun)
    try {
      const g = await fetchGlobalExplain()
      globalExplain.value = g.data
    } catch {
      globalExplain.value = null
    }
    try {
      const cal = await fetchCalibration(CALIB_RUN)
      calibration.value = cal.data
    } catch {
      calibration.value = null
    }
  } catch (e) {
    metrics.value = null
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
      title="模型实验室"
      description="E0–E8 全量矩阵：PR-AUC 主指标 + CV/CI 显著性 + 校准 + 阈值成本分析。阈值在 valid 搜索、test 一次评估。"
    >
      <template #actions>
        <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
      </template>
    </PageHeaderBar>

    <p class="disclaimer">
      主指标顺序：PR-AUC → ROC-AUC → F1 → 混淆矩阵。Accuracy 在高正类比下易虚高，须与 Dummy 对照。
      CI 重叠的 run 之间不能宣称「更优」；E5/E6 为消融实验，不参选默认 run。
    </p>

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <ElCard v-else-if="items.length" shadow="never" class="section-card">
      <template #header>
        <span>实验矩阵对比</span>
        <span class="muted mono" style="margin-left: 12px">primary = {{ metrics?.primary_metric }}</span>
      </template>
      <ElTable :data="items" size="small" stripe>
        <ElTableColumn prop="run_id" label="run_id" min-width="170">
          <template #default="{ row }">
            <span class="mono">{{ row.run_id }}</span>
            <ElTag v-if="isDummy(row)" size="small" type="info" style="margin-left: 6px">Dummy</ElTag>
            <ElTag v-else-if="isAblation(row)" size="small" type="warning" style="margin-left: 6px">
              消融·不作默认
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="PR-AUC" width="100">
          <template #default="{ row }">
            <strong
              class="tabular-nums"
              :class="{ best: bestPr != null && row.pr_auc === bestPr && !isDummy(row) && !isAblation(row) }"
            >
              {{ formatMetric(row.pr_auc as number | undefined) }}
            </strong>
          </template>
        </ElTableColumn>
        <ElTableColumn label="CV 5-fold" width="140">
          <template #default="{ row }">
            <span v-if="row.cv_pr_auc_mean != null" class="tabular-nums">
              {{ formatMetric(row.cv_pr_auc_mean as number) }}±{{ formatMetric(row.cv_pr_auc_std as number, 4) }}
            </span>
            <span v-else class="muted">—</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="95% CI（bootstrap）" min-width="170">
          <template #default="{ row }">
            <span v-if="row.pr_auc_ci_low != null" class="tabular-nums">
              [{{ formatMetric(row.pr_auc_ci_low as number) }}, {{ formatMetric(row.pr_auc_ci_high as number) }}]
            </span>
            <span v-else class="muted">—</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="ROC-AUC" width="100">
          <template #default="{ row }">
            <span class="tabular-nums">{{ formatMetric(row.roc_auc as number | undefined) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="F1" width="90">
          <template #default="{ row }">
            <span class="tabular-nums">{{ formatMetric(row.f1 as number | undefined) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="Brier" width="90">
          <template #default="{ row }">
            <span v-if="row.brier != null" class="tabular-nums">{{ formatMetric(row.brier as number) }}</span>
            <span v-else class="muted">—</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="Accuracy（对照）" width="130">
          <template #default="{ row }">
            <span class="tabular-nums muted">{{ formatMetric(row.accuracy as number | undefined) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="阈值" width="80">
          <template #default="{ row }">
            <span class="tabular-nums">{{ formatMetric(row.threshold as number | undefined, 3) }}</span>
          </template>
        </ElTableColumn>
      </ElTable>
      <p class="muted" style="margin-top: 12px">{{ metrics?.accuracy_note }}</p>
    </ElCard>

    <EmptyState
      v-else-if="!loading && !error"
      title="尚无 metrics"
      description="请运行 python scripts/06_train_full.py"
    />

    <ElCard v-if="items.length" shadow="never" class="section-card">
      <template #header>
        <span>评估曲线</span>
        <ElSelect
          v-model="selectedRun"
          size="small"
          style="width: 260px; margin-left: 12px"
          @change="loadRunDetail"
        >
          <ElOption
            v-for="r in items.filter((x) => !x.skipped)"
            :key="r.run_id"
            :label="r.run_id"
            :value="r.run_id"
          />
        </ElSelect>
      </template>
      <div class="grid-2">
        <RocPrCurveChart
          v-if="curves"
          :pr="curves.pr_curve"
          :roc="curves.roc_curve"
          :pr-auc="curves.pr_auc"
          :roc-auc="curves.roc_auc"
        />
        <div v-if="confusion">
          <div class="title">混淆矩阵（test · 阈值 {{ formatMetric(detail?.threshold as number | undefined, 2) }}）</div>
          <ConfusionHeatmap :confusion="confusion" />
        </div>
        <LiftChart v-if="lift" :deciles="lift.lift_deciles" title="营销升降表（lift / 累计捕获率）" />
      </div>
    </ElCard>

    <ElCard v-if="scan" shadow="never" class="section-card">
      <template #header>
        <span>阈值-成本分析</span>
        <span class="muted" style="margin-left: 12px">{{ scan.cost_note }}</span>
      </template>
      <ThresholdScanChart
        :rows="scan.rows"
        :current-threshold="scan.current_threshold"
        :best-cost-threshold="scan.best_by_cost?.threshold"
        :selected-threshold="sliderThreshold"
        :cost-fn="scan.cost_fn"
        :cost-fp="scan.cost_fp"
      />
      <div class="slider-row">
        <span class="muted">阈值 {{ sliderThreshold.toFixed(2) }}</span>
        <ElSlider
          v-model="sliderThreshold"
          :min="0.05"
          :max="0.95"
          :step="0.01"
          style="flex: 1"
        />
        <span v-if="sliderRow" class="tabular-nums muted">
          P={{ sliderRow.precision.toFixed(4) }} R={{ sliderRow.recall.toFixed(4) }}
          F1={{ sliderRow.f1.toFixed(4) }} 成本={{ sliderRow.expected_cost.toFixed(0) }}
        </span>
      </div>
    </ElCard>

    <ElCard v-if="calibration" shadow="never" class="section-card">
      <template #header>
        <span>概率校准（{{ calibration.run_id }}）</span>
        <span class="muted" style="margin-left: 12px">{{ calibration.note }}</span>
      </template>
      <CalibrationChart :before="calibration.before" :after="calibration.after" :method="calibration.method" />
      <p class="muted tabular-nums" style="margin-top: 8px">
        brier {{ calibration.before.brier.toFixed(4) }} → {{ calibration.after.brier.toFixed(4) }}；
        log_loss {{ calibration.before.log_loss.toFixed(4) }} → {{ calibration.after.log_loss.toFixed(4) }}
      </p>
    </ElCard>

    <ElCard v-if="shapItems.length" shadow="never" class="section-card">
      <template #header>
        全局特征贡献
        <span class="muted mono" style="margin-left: 12px">
          {{ globalExplain?.run_id }} · {{ globalExplain?.method }}
        </span>
      </template>
      <ShapBarChart :items="shapItems" />
    </ElCard>
  </div>
</template>

<style scoped>
.best {
  color: var(--color-primary);
}
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 1100px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
.title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}
.slider-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}
</style>
