<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElCollapse,
  ElCollapseItem,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
  ElSpace,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { fetchFeatureMeta, type FeatureMetaData } from '../api/data'
import { predict, predictBatch, type BatchPredictData, type PredictData } from '../api/models'
import {
  explainCounterfactual, explainCustomer,
  type CounterfactualData, type CustomerExplainData,
} from '../api/explain'
import CounterfactualCurveChart from '../components/CounterfactualCurveChart.vue'
import DisclaimerBanner from '../components/DisclaimerBanner.vue'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import PredictResultCard from '../components/PredictResultCard.vue'
import ShapBarChart from '../components/ShapBarChart.vue'
import { formatProba } from '../utils/format'

const loading = ref(false)
const metaLoading = ref(true)
const error = ref<string | null>(null)
const meta = ref<FeatureMetaData | null>(null)
const customerId = ref<number | null>(8000)
const form = reactive<Record<string, string | number>>({})
const pred = ref<PredictData | null>(null)
const expl = ref<CustomerExplainData | null>(null)
const batchIds = ref('8000,8001,8002')
const batchResult = ref<BatchPredictData | null>(null)
const batchLoading = ref(false)

// 反事实（模型行为口径）：沿用最近一次预测的输入
const lastInput = ref<{ customer_id?: number; features?: Record<string, unknown> } | null>(null)
const cfFeature = ref<string>('')
const cfOpen = ref<string[]>(['cf-curve']) // Stage 6：反事实曲线默认展开，步骤表保持折叠
const cfTarget = ref(0.9)
const cfLoading = ref(false)
const cfError = ref<string | null>(null)
const cf = ref<CounterfactualData | null>(null)

async function runCounterfactual() {
  if (!lastInput.value || !cfFeature.value) return
  cfLoading.value = true
  cfError.value = null
  cf.value = null
  try {
    const r = await explainCounterfactual({
      ...lastInput.value,
      feature: cfFeature.value,
      target_proba: cfTarget.value,
      run_id: pred.value?.run_id,
    })
    cf.value = r.data
  } catch (e) {
    cfError.value = e instanceof Error ? e.message : '反事实分析失败'
  } finally {
    cfLoading.value = false
  }
}

function applyDefaults(m: FeatureMetaData) {
  Object.keys(form).forEach((k) => delete form[k])
  for (const [k, v] of Object.entries(m.sample_defaults || {})) {
    form[k] = v
  }
}

async function loadMeta() {
  metaLoading.value = true
  error.value = null
  try {
    const res = await fetchFeatureMeta()
    meta.value = res.data
    applyDefaults(res.data)
    if (!cfFeature.value) cfFeature.value = res.data.numeric_features?.[0] ?? ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载特征失败'
  } finally {
    metaLoading.value = false
  }
}

async function runPredict(byId: boolean) {
  loading.value = true
  error.value = null
  pred.value = null
  expl.value = null
  try {
    const body = byId
      ? { customer_id: customerId.value ?? undefined }
      : { features: { ...form } }
    const p = await predict(body)
    pred.value = p.data
    lastInput.value = body as { customer_id?: number; features?: Record<string, unknown> }
    cf.value = null
    cfError.value = null
    const e = await explainCustomer({
      ...body,
      top_k: 10,
      run_id: p.data.run_id,
    })
    expl.value = e.data
  } catch (e) {
    error.value = e instanceof Error ? e.message : '预测失败'
  } finally {
    loading.value = false
  }
}

async function runBatch() {
  batchLoading.value = true
  error.value = null
  batchResult.value = null
  try {
    const ids = batchIds.value
      .split(/[,，\s]+/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => Number(s))
      .filter((n) => Number.isFinite(n))
    const r = await predictBatch({ customer_ids: ids })
    batchResult.value = r.data
  } catch (e) {
    error.value = e instanceof Error ? e.message : '批量预测失败'
  } finally {
    batchLoading.value = false
  }
}

onMounted(loadMeta)
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="客户洞察"
      description="按 CustomerID 或特征表单预测转化概率，并展示局部贡献（非严格因果）。"
    >
      <template #actions>
        <ElButton :loading="metaLoading" @click="loadMeta">重载特征</ElButton>
      </template>
    </PageHeaderBar>

    <DisclaimerBanner content="预测、SHAP 与反事实只描述模型行为；反事实面板用于敏感性分析，不构成因果效应或投放建议。" />
    <ErrorState v-if="error" :message="error" @retry="loadMeta" />

    <div v-else class="layout-2">
      <ElCard shadow="never" class="section-card">
        <template #header>输入</template>
        <ElSpace wrap>
          <span class="muted">CustomerID</span>
          <ElInputNumber v-model="customerId" :min="1" :controls="false" />
          <ElButton type="primary" :loading="loading" @click="runPredict(true)">按 ID 预测</ElButton>
        </ElSpace>
        <p class="muted m-block-md">或填写特征（样例默认已填充）：</p>
        <ElForm v-if="meta" label-position="top" class="feat-form">
          <ElFormItem
            v-for="col in meta.feature_columns_raw"
            :key="col"
            :label="col"
          >
            <ElSelect
              v-if="meta.categorical_features.includes(col)"
              v-model="form[col]"
              filterable
              allow-create
              class="w-full"
            >
              <ElOption
                v-if="form[col] != null"
                :label="String(form[col])"
                :value="form[col]"
              />
            </ElSelect>
            <ElInputNumber
              v-else-if="meta.numeric_features.includes(col) || meta.flag_features.includes(col)"
              v-model="form[col] as number"
              :controls="false"
              class="w-full"
            />
            <ElInput v-else v-model="form[col] as string" />
          </ElFormItem>
        </ElForm>
        <EmptyState v-else-if="!metaLoading" title="缺少特征 schema" description="请先训练生成 feature_schema.json" />
        <ElSpace class="mt-sm">
          <ElButton v-if="meta" @click="applyDefaults(meta)">填充样例</ElButton>
          <ElButton type="primary" :loading="loading" :disabled="!meta" @click="runPredict(false)">
            按特征预测
          </ElButton>
        </ElSpace>
      </ElCard>

      <div>
        <PredictResultCard v-if="pred" :result="pred" class="section-card" />

        <ElCard v-if="expl?.top_features?.length" shadow="never" class="section-card">
          <template #header>
            局部解释
            <span class="muted mono ml-sm">{{ expl.method }}</span>
          </template>
          <ShapBarChart
            :items="
              expl.top_features.map((f) => ({
                name: f.name,
                value: Number(f.shap_value ?? f.mean_abs_shap ?? 0),
              }))
            "
          />
        </ElCard>

        <!-- Stage 6 叙事降级：反事实收进折叠区默认收起（端点与代码保留，演示时手动展开） -->
        <ElCollapse v-if="pred" v-model="cfOpen" class="section-card cf-collapse">
          <ElCollapseItem
            name="cf"
            title="反事实分析 · 模型行为分析（敏感性），非因果，不构成投放建议"
          >
          <ElSpace wrap class="w-full">
            <span class="muted">扰动特征</span>
            <ElSelect v-model="cfFeature" class="cf-feature-select">
              <ElOption
                v-for="f in meta?.numeric_features ?? []"
                :key="f"
                :label="f"
                :value="f"
              />
            </ElSelect>
            <span class="muted">目标 proba</span>
            <ElInputNumber v-model="cfTarget" :min="0.05" :max="0.99" :step="0.05" :controls="false" />
            <ElButton type="primary" :loading="cfLoading" :disabled="!cfFeature" @click="runCounterfactual">
              分析
            </ElButton>
          </ElSpace>
          <p v-if="cfError" class="err-text">{{ cfError }}</p>
          <template v-if="cf">
            <CounterfactualCurveChart
              v-if="cf.curve"
              :feature="cf.curve.feature"
              :grid="cf.curve.grid"
              :proba="cf.curve.proba"
              :base-value="cf.curve.base_value"
              :base-proba="cf.curve.base_proba"
              :target-proba="cfTarget"
            />
            <div v-if="cf.counterfactual" class="cf-block">
              <div class="cf-head">
                <ElTag :type="cf.counterfactual.achieved ? 'success' : 'warning'" size="small">
                  {{ cf.counterfactual.achieved ? '可达目标' : '步数上限内未达标' }}
                </ElTag>
                <span class="tabular-nums muted">
                  base {{ cf.counterfactual.base_proba.toFixed(4) }} →
                  final {{ cf.counterfactual.final_proba.toFixed(4) }} ·
                  {{ cf.counterfactual.n_steps }} 步
                </span>
              </div>
              <ElTable v-if="cf.counterfactual.steps.length" :data="cf.counterfactual.steps" size="small">
                <ElTableColumn prop="feature" label="特征" min-width="140" />
                <ElTableColumn label="从" width="110">
                  <template #default="{ row }"><span class="tabular-nums">{{ row.from.toFixed(3) }}</span></template>
                </ElTableColumn>
                <ElTableColumn label="改为" width="110">
                  <template #default="{ row }"><span class="tabular-nums">{{ row.to.toFixed(3) }}</span></template>
                </ElTableColumn>
                <ElTableColumn label="改动后 proba" width="130">
                  <template #default="{ row }"><span class="tabular-nums">{{ row.proba_after.toFixed(4) }}</span></template>
                </ElTableColumn>
              </ElTable>
              <p class="muted">{{ cf.counterfactual.disclaimer }}</p>
            </div>
          </template>
          </ElCollapseItem>
        </ElCollapse>

        <EmptyState
          v-if="!pred && !loading"
          title="尚未预测"
          description="输入 CustomerID（如 8000）或使用样例特征后点击预测。"
        />

        <ElCard shadow="never" class="section-card">
          <template #header>批量预测（上限 200）</template>
          <p class="muted mt-0">逗号分隔 CustomerID；结果仅供名单筛选参考，非因果。</p>
          <ElSpace wrap class="w-full">
            <ElInput v-model="batchIds" class="input-wide" placeholder="8000,8001,8002" />
            <ElButton type="primary" :loading="batchLoading" @click="runBatch">批量预测</ElButton>
          </ElSpace>
          <div v-if="batchResult" class="batch-box">
            <div class="muted mono">
              ok={{ batchResult.n_ok }}/{{ batchResult.n_requested }} · thr={{ formatProba(batchResult.threshold) }} ·
              {{ batchResult.run_id }}
            </div>
            <ul class="batch-list">
              <li v-for="(it, i) in batchResult.items" :key="i" class="mono">
                id={{ it.customer_id }} proba={{ formatProba(it.proba) }} label={{ it.label }}
              </li>
            </ul>
            <ul v-if="batchResult.errors?.length" class="batch-list err">
              <li v-for="(er, i) in batchResult.errors" :key="'e' + i">
                id={{ er.customer_id }} {{ er.message }}
              </li>
            </ul>
          </div>
        </ElCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout-2 {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: var(--space-3);
}
@media (max-width: 992px) {
  .layout-2 {
    grid-template-columns: 1fr;
  }
}
.feat-form {
  max-height: 420px;
  overflow: auto;
  padding-right: 4px;
}
.batch-box {
  margin-top: var(--space-3);
}
.batch-list {
  margin: var(--space-2) 0 0;
  padding-left: var(--space-5);
  max-height: 160px;
  overflow: auto;
}
.batch-list.err {
  color: var(--el-color-danger);
}
.cf-block {
  margin-top: var(--space-3);
}
.cf-head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}
.err-text {
  color: var(--color-danger-text);
  font-size: var(--font-size-sm);
}
.cf-feature-select { width: 200px; }
</style>
