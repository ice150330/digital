<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ElButton, ElCard, ElInputNumber, ElSpace, ElTable, ElTableColumn, ElTag,
} from 'element-plus'
import { simulateBudget, type BudgetSimulateData } from '../api/simulate'
import BudgetCurveChart from '../components/BudgetCurveChart.vue'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import KpiCard from '../components/KpiCard.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import { formatInt } from '../utils/format'

const loading = ref(false)
const exporting = ref(false)
const error = ref<string | null>(null)
const data = ref<BudgetSimulateData | null>(null)

const valuePerConversion = ref(10)
const costPerContact = ref(4)
const budget = ref<number | null>(null)

async function run(exportCsv = false) {
  if (exportCsv) exporting.value = true
  else loading.value = true
  error.value = null
  try {
    const r = await simulateBudget({
      value_per_conversion: valuePerConversion.value,
      cost_per_contact: costPerContact.value,
      budget: budget.value ?? undefined,
      export: exportCsv,
    })
    data.value = r.data
  } catch (e) {
    error.value = e instanceof Error ? e.message : '模拟失败'
  } finally {
    loading.value = false
    exporting.value = false
  }
}

onMounted(() => run())
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="预算分配模拟"
      description="期望值口径：proba × 单客价值 − 触达成本，按期望价值排序后扫描触达人数 K。"
    >
      <template #actions>
        <ElSpace>
          <ElButton :loading="exporting" :disabled="!data" @click="run(true)">导出名单 CSV</ElButton>
          <ElButton type="primary" :loading="loading" @click="run()">运行模拟</ElButton>
        </ElSpace>
      </template>
    </PageHeaderBar>

    <p class="disclaimer">
      {{ data?.disclaimer || '期望值为排序参考，非因果收益承诺；单客价值与触达成本为业务假设参数。' }}
    </p>

    <ElCard shadow="never" class="section-card">
      <template #header>参数</template>
      <ElSpace wrap size="large">
        <label class="param">
          <span class="muted">单客转化价值</span>
          <ElInputNumber v-model="valuePerConversion" :min="0.1" :step="1" :controls="false" />
        </label>
        <label class="param">
          <span class="muted">单次触达成本</span>
          <ElInputNumber v-model="costPerContact" :min="0.1" :step="0.5" :controls="false" />
        </label>
        <label class="param">
          <span class="muted">预算上限（可空）</span>
          <ElInputNumber v-model="budget" :min="0" :step="100" :controls="false" placeholder="全量扫描" />
        </label>
        <span class="muted">
          盈亏平衡 proba = {{ (costPerContact / Math.max(valuePerConversion, 1e-9)).toFixed(3) }}
        </span>
      </ElSpace>
    </ElCard>

    <ErrorState v-if="error" :message="error" @retry="run()" />

    <template v-if="data">
      <div class="kpis">
        <KpiCard label="推荐触达人数 K" :value="formatInt(data.recommended_k)" hint="期望净收益最大（净>0）" />
        <KpiCard
          label="期望净收益"
          :value="data.recommended ? data.recommended.expected_net.toFixed(1) : '—'"
          :hint="`毛收益 ${data.recommended?.expected_revenue?.toFixed(1) ?? '—'} − 成本`"
        />
        <KpiCard
          label="期望转化数"
          :value="data.recommended ? data.recommended.expected_conversions.toFixed(1) : '—'"
          :hint="`人群均值 proba ${data.recommended?.avg_proba?.toFixed(3) ?? '—'}`"
        />
        <KpiCard
          label="评估人群（test）"
          :value="formatInt(data.n_population)"
          :hint="`${data.run_id}${data.calibrated ? ' · 已校准' : ''}`"
        />
      </div>

      <ElCard shadow="never" class="section-card">
        <template #header>期望收益曲线</template>
        <BudgetCurveChart :points="data.curve" :recommended-k="data.recommended_k" :budget="budget" />
      </ElCard>

      <ElCard v-if="data.top_list?.length" shadow="never" class="section-card">
        <template #header>
          Top 名单预览（前 {{ data.top_list.length }} / 推荐 K={{ formatInt(data.recommended_k) }}）
          <ElTag v-if="data.export_path" size="small" type="success">
            已导出 {{ data.export_path }}
          </ElTag>
        </template>
        <ElTable :data="data.top_list" size="small" stripe max-height="380">
          <ElTableColumn prop="rank" label="#" width="70" />
          <ElTableColumn label="CustomerID" width="120">
            <template #default="{ row }"><span class="mono">{{ row.customerid ?? '—' }}</span></template>
          </ElTableColumn>
          <ElTableColumn label="proba" width="120">
            <template #default="{ row }"><span class="tabular-nums">{{ row.proba.toFixed(4) }}</span></template>
          </ElTableColumn>
          <ElTableColumn label="期望价值" min-width="120">
            <template #default="{ row }"><span class="tabular-nums">{{ row.expected_value.toFixed(3) }}</span></template>
          </ElTableColumn>
        </ElTable>
      </ElCard>
    </template>

    <EmptyState
      v-else-if="!loading && !error"
      title="尚无模拟结果"
      description="请确认 test.csv 与模型产物就绪（python scripts/06_train_full.py）。"
    />
  </div>
</template>

<style scoped>
.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
@media (max-width: 992px) {
  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }
}
.param {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
