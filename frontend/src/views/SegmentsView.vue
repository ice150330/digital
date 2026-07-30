<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElButton, ElCard, ElInputNumber, ElSpace, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { assignSegment, fetchSegments, type SegmentsData } from '../api/segments'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import { formatInt, formatPercent } from '../utils/format'

const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<SegmentsData | null>(null)
const customerId = ref<number>(8000)
const assignResult = ref<string>('')

async function load() {
  loading.value = true
  error.value = null
  try {
    const r = await fetchSegments()
    data.value = r.data
  } catch (e) {
    data.value = null
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function doAssign() {
  try {
    const r = await assignSegment({ customer_id: customerId.value })
    assignResult.value = `cluster_id=${r.data.cluster_id}` + (r.data.distance != null ? ` distance=${r.data.distance.toFixed(4)}` : '')
  } catch (e) {
    assignResult.value = e instanceof Error ? e.message : '分配失败'
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="分群画像"
      description="K-Means 分群；训练特征不含 Conversion，簇转化率为事后统计。"
    >
      <template #actions>
        <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
      </template>
    </PageHeaderBar>

    <p class="disclaimer">
      {{ data?.disclaimer || '分群用于探索画像，簇间转化率差异不等于因果效应。' }}
    </p>

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <template v-else-if="data">
      <ElCard shadow="never" class="section-card">
        <template #header>
          簇列表
          <span class="muted mono" style="margin-left: 8px">
            {{ data.method }} · k={{ data.n_clusters }} · n={{ formatInt(data.n_samples) }}
          </span>
          <ElTag v-if="data.label_excluded" size="small" type="success" style="margin-left: 8px">
            训练无标签
          </ElTag>
        </template>
        <ElTable :data="data.clusters" size="small" stripe>
          <ElTableColumn prop="cluster_id" label="簇" width="80" />
          <ElTableColumn label="人数" width="100">
            <template #default="{ row }">{{ formatInt(row.n) }}</template>
          </ElTableColumn>
          <ElTableColumn label="占比" width="100">
            <template #default="{ row }">{{ formatPercent(row.share) }}</template>
          </ElTableColumn>
          <ElTableColumn label="事后转化率" width="120">
            <template #default="{ row }">{{ formatPercent(row.conversion_rate) }}</template>
          </ElTableColumn>
          <ElTableColumn label="画像均值（节选）">
            <template #default="{ row }">
              <span class="mono muted">
                Age={{ row.profile_means?.Age?.toFixed?.(1) ?? '—' }},
                AdSpend={{ row.profile_means?.AdSpend?.toFixed?.(0) ?? '—' }},
                EmailOpens={{ row.profile_means?.EmailOpens?.toFixed?.(1) ?? '—' }}
              </span>
            </template>
          </ElTableColumn>
        </ElTable>
      </ElCard>

      <ElCard shadow="never" class="section-card">
        <template #header>分配客户到簇</template>
        <ElSpace>
          <ElInputNumber v-model="customerId" :min="1" />
          <ElButton @click="doAssign">分配</ElButton>
          <span class="mono">{{ assignResult }}</span>
        </ElSpace>
      </ElCard>
    </template>

    <EmptyState
      v-else-if="!loading"
      title="分群尚未就绪"
      description="请运行 python scripts/04_train_cluster.py"
    />
  </div>
</template>
