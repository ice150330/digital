<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElButton, ElCard, ElInputNumber, ElSpace, ElTable, ElTableColumn } from 'element-plus'
import { fetchRules, type RulesData } from '../api/rules'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import { formatMetric } from '../utils/format'

const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<RulesData | null>(null)
const minLift = ref(1.05)

async function load() {
  loading.value = true
  error.value = null
  try {
    const r = await fetchRules(minLift.value, 50)
    data.value = r.data
  } catch (e) {
    data.value = null
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
      title="关联规则"
      description="分箱后的关联规则；展示 support / confidence / lift。"
    >
      <template #actions>
        <ElSpace>
          <span class="muted">min lift</span>
          <ElInputNumber v-model="minLift" :step="0.05" :min="0" :max="10" />
          <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
        </ElSpace>
      </template>
    </PageHeaderBar>

    <p class="disclaimer">
      {{ data?.disclaimer || '关联规则表达的是相关而非因果，不可直接当作投放因果结论。' }}
    </p>

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <ElCard v-else-if="data?.rules?.length" shadow="never" class="section-card">
      <template #header>
        规则表
        <span class="muted mono ml-sm">
          {{ data.method }} · n={{ data.n_rules }}
        </span>
      </template>
      <ElTable :data="data.rules" size="small" stripe>
        <ElTableColumn prop="antecedents" label="前件" min-width="160" />
        <ElTableColumn prop="consequents" label="后件" min-width="140" />
        <ElTableColumn label="support" width="100">
          <template #default="{ row }">
            <span class="tabular-nums">{{ formatMetric(row.support) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="confidence" width="110">
          <template #default="{ row }">
            <span class="tabular-nums">{{ formatMetric(row.confidence) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="lift" width="90">
          <template #default="{ row }">
            <strong class="tabular-nums">{{ formatMetric(row.lift) }}</strong>
          </template>
        </ElTableColumn>
      </ElTable>
    </ElCard>

    <EmptyState
      v-else-if="!loading && !error"
      title="规则尚未就绪"
      description="请运行 python scripts/05_mine_rules.py"
    />
  </div>
</template>
