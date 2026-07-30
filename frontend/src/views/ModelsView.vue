<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElButton, ElCard, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { fetchMetrics, type MetricRow, type MetricsListData } from '../api/models'
import { fetchGlobalExplain, type GlobalExplainData } from '../api/explain'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import ShapBarChart from '../components/ShapBarChart.vue'
import { formatMetric } from '../utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const metrics = ref<MetricsListData | null>(null)
const globalExplain = ref<GlobalExplainData | null>(null)

const items = computed(() => metrics.value?.items ?? [])

const bestPr = computed(() => {
  const vals = items.value.map((r) => r.pr_auc).filter((v): v is number => v != null)
  return vals.length ? Math.max(...vals) : null
})

const shapItems = computed(() =>
  (globalExplain.value?.top_features ?? []).map((f) => ({
    name: f.name,
    value: Number(f.mean_abs_shap ?? f.shap_value ?? 0),
  })),
)

function isDummy(row: MetricRow | Record<string, unknown>) {
  return (
    String(row.exp_id || '').toUpperCase() === 'E0' ||
    /dummy/i.test(String(row.model_name || ''))
  )
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const m = await fetchMetrics()
    metrics.value = m.data
    try {
      const g = await fetchGlobalExplain()
      globalExplain.value = g.data
    } catch {
      globalExplain.value = null
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
      description="以 PR-AUC 为主指标；Accuracy 仅对照，请并列 Dummy。阈值在 valid 搜索、test 一次评估。"
    >
      <template #actions>
        <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
      </template>
    </PageHeaderBar>

    <p class="disclaimer">
      主指标顺序：PR-AUC → ROC-AUC → F1 → 混淆矩阵。Accuracy 在高正类比下易虚高，须与 Dummy 对照。
    </p>

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <ElCard v-else-if="items.length" shadow="never" class="section-card">
      <template #header>
        <span>实验对比</span>
        <span class="muted mono" style="margin-left: 12px">primary = {{ metrics?.primary_metric }}</span>
      </template>
      <ElTable :data="items" size="small" stripe>
        <ElTableColumn prop="run_id" label="run_id" min-width="180" />
        <ElTableColumn prop="exp_id" label="实验" width="80" />
        <ElTableColumn prop="model_name" label="模型" width="140" />
        <ElTableColumn label="PR-AUC" width="110">
          <template #default="{ row }">
            <strong
              class="tabular-nums"
              :class="{ best: bestPr != null && row.pr_auc === bestPr && !isDummy(row) }"
            >
              {{ formatMetric(row.pr_auc as number | undefined) }}
            </strong>
          </template>
        </ElTableColumn>
        <ElTableColumn label="ROC-AUC" width="110">
          <template #default="{ row }">
            <span class="tabular-nums">{{ formatMetric(row.roc_auc as number | undefined) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="F1" width="100">
          <template #default="{ row }">
            <span class="tabular-nums">{{ formatMetric(row.f1 as number | undefined) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="Accuracy（对照）" width="140">
          <template #default="{ row }">
            <span class="tabular-nums muted">{{ formatMetric(row.accuracy as number | undefined) }}</span>
            <ElTag v-if="isDummy(row)" size="small" type="info" style="margin-left: 6px">Dummy</ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="阈值" width="90">
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
      description="请运行 python scripts/02_train_classify.py"
    />

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
</style>
