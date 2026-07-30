<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
  ElSpace,
  ElTag,
} from 'element-plus'
import { fetchFeatureMeta, type FeatureMetaData } from '../api/data'
import { predict, type PredictData } from '../api/models'
import { explainCustomer, type CustomerExplainData } from '../api/explain'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
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

    <ErrorState v-if="error" :message="error" @retry="loadMeta" />

    <div v-else class="layout-2">
      <ElCard shadow="never" class="section-card">
        <template #header>输入</template>
        <ElSpace wrap>
          <span class="muted">CustomerID</span>
          <ElInputNumber v-model="customerId" :min="1" :controls="false" />
          <ElButton type="primary" :loading="loading" @click="runPredict(true)">按 ID 预测</ElButton>
        </ElSpace>
        <p class="muted" style="margin: 12px 0">或填写特征（样例默认已填充）：</p>
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
              style="width: 100%"
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
              style="width: 100%"
            />
            <ElInput v-else v-model="form[col] as string" />
          </ElFormItem>
        </ElForm>
        <EmptyState v-else-if="!metaLoading" title="缺少特征 schema" description="请先训练生成 feature_schema.json" />
        <ElSpace style="margin-top: 8px">
          <ElButton v-if="meta" @click="applyDefaults(meta)">填充样例</ElButton>
          <ElButton type="primary" :loading="loading" :disabled="!meta" @click="runPredict(false)">
            按特征预测
          </ElButton>
        </ElSpace>
      </ElCard>

      <div>
        <ElCard v-if="pred" shadow="never" class="section-card">
          <template #header>预测结果</template>
          <div class="result">
            <div>
              <div class="muted">proba</div>
              <div class="big tabular-nums">{{ formatProba(pred.proba) }}</div>
            </div>
            <div>
              <div class="muted">label</div>
              <ElTag :type="pred.label === 1 ? 'success' : 'info'" size="large">
                {{ pred.label === 1 ? '转化' : '未转化' }}
              </ElTag>
            </div>
            <div>
              <div class="muted">threshold</div>
              <div class="tabular-nums">{{ formatProba(pred.threshold) }}</div>
            </div>
            <div>
              <div class="muted">run_id</div>
              <div class="mono">{{ pred.run_id }}</div>
            </div>
          </div>
        </ElCard>

        <ElCard v-if="expl?.top_features?.length" shadow="never" class="section-card">
          <template #header>
            局部解释
            <span class="muted mono" style="margin-left: 8px">{{ expl.method }}</span>
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

        <EmptyState
          v-if="!pred && !loading"
          title="尚未预测"
          description="输入 CustomerID（如 8000）或使用样例特征后点击预测。"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout-2 {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 16px;
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
.result {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.big {
  font-size: 28px;
  font-weight: 700;
}
</style>
