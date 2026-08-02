<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElButton, ElCard, ElInputNumber, ElSpace, ElTable, ElTableColumn, ElTag } from 'element-plus'
import {
  assignSegment, fetchSegmentCompare, fetchSegmentProjection, fetchSegments,
  type SegmentCompareData, type SegmentProjectionData, type SegmentsData,
} from '../api/segments'
import EmptyState from '../components/EmptyState.vue'
import DisclaimerBanner from '../components/DisclaimerBanner.vue'
import ErrorState from '../components/ErrorState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
import ScatterPcaChart from '../components/ScatterPcaChart.vue'
import SegmentCard from '../components/SegmentCard.vue'
import { formatInt } from '../utils/format'

const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<SegmentsData | null>(null)
const compare = ref<SegmentCompareData | null>(null)
const projection = ref<SegmentProjectionData | null>(null)
const customerId = ref<number>(8000)
const assignResult = ref<string>('')

const autoNames = computed(() => compare.value?.auto_names ?? {})
const stabilityBadge = computed(() => {
  const s = compare.value?.stability
  if (!s) return null
  return { type: s.ari_mean >= 0.75 ? 'success' : s.ari_mean >= 0.5 ? 'primary' : 'warning', ...s }
})

async function load() {
  loading.value = true
  error.value = null
  try {
    const r = await fetchSegments()
    data.value = r.data
    try {
      const c = await fetchSegmentCompare()
      compare.value = c.data
    } catch {
      compare.value = null
    }
    try {
      const p = await fetchSegmentProjection()
      projection.value = p.data
    } catch {
      projection.value = null
    }
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
      description="多算法分群对比 + 稳定性评估 + PCA 投影；训练特征不含 Conversion，簇转化率为事后统计。"
    >
      <template #actions>
        <ElButton type="primary" :loading="loading" @click="load">刷新</ElButton>
      </template>
    </PageHeaderBar>

    <DisclaimerBanner :content="data?.disclaimer || '分群用于探索画像，簇间转化率差异不等于因果效应。'" />

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <template v-else-if="data">
      <ElCard shadow="never" class="section-card">
        <template #header>
          簇列表
          <span class="muted mono ml-sm">
            {{ data.method }} · k={{ data.n_clusters }} · n={{ formatInt(data.n_samples) }}
          </span>
          <ElTag v-if="data.label_excluded" size="small" type="success">
            训练无标签
          </ElTag>
          <ElTag
            v-if="stabilityBadge"
            size="small"
            :type="stabilityBadge.type as 'success' | 'primary' | 'warning'"

            :title="`bootstrap ${stabilityBadge.n_boot} 次 ARI：${stabilityBadge.note || '划分配对稳定性'}`"
          >
            稳定性 ARI {{ stabilityBadge.ari_mean.toFixed(3) }}±{{ stabilityBadge.ari_std.toFixed(3) }}
          </ElTag>
        </template>
        <div class="segment-grid">
          <SegmentCard
            v-for="cluster in data.clusters"
            :key="cluster.cluster_id"
            :cluster="cluster"
            :name="autoNames[String(cluster.cluster_id)]"
            :stability="stabilityBadge?.ari_mean"
          />
        </div>
      </ElCard>

      <ElCard v-if="projection?.points?.length" shadow="never" class="section-card">
        <template #header>
          PCA 二维投影
          <span class="muted ml-sm">
            方差解释率
            {{ projection.explained_variance.map((v) => (v * 100).toFixed(1) + '%').join(' + ') }}
            · n={{ formatInt(projection.n_points) }}
          </span>
        </template>
        <ScatterPcaChart :points="projection.points" :auto-names="autoNames" />
        <p class="muted mb-0">PCA 仅用于可视化，不参与分群训练；相关非因果。</p>
      </ElCard>

      <ElCard v-if="compare?.comparison?.length" shadow="never" class="section-card">
        <template #header>
          多算法对比（KMeans / GMM / Agglomerative × K）
          <span class="muted ml-sm">主分群：KMeans k={{ compare.kmeans_k }}</span>
        </template>
        <ElTable :data="compare.comparison" size="small" stripe max-height="360">
          <ElTableColumn prop="algo" label="算法" width="140">
            <template #default="{ row }"><span class="mono">{{ row.algo }}</span></template>
          </ElTableColumn>
          <ElTableColumn prop="k" label="K" width="70" />
          <ElTableColumn label="Silhouette" width="120">
            <template #default="{ row }">
              <strong v-if="row.algo === 'kmeans' && row.k === compare.kmeans_k" class="tabular-nums">
                {{ row.silhouette?.toFixed(4) ?? '—' }}
              </strong>
              <span v-else class="tabular-nums">{{ row.silhouette?.toFixed(4) ?? '—' }}</span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="CH 指数" width="120">
            <template #default="{ row }">
              <span class="tabular-nums">{{ row.calinski_harabasz?.toFixed(1) ?? '—' }}</span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="BIC（GMM）" width="130">
            <template #default="{ row }">
              <span class="tabular-nums">{{ row.bic != null ? row.bic.toFixed(0) : '—' }}</span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="备注" min-width="140">
            <template #default="{ row }">
              <span v-if="row.error" class="err-text">{{ row.error }}</span>
              <ElTag
                v-else-if="row.algo === 'kmeans' && row.k === compare.kmeans_k"
                size="small" type="success"
              >
                当前主分群
              </ElTag>
            </template>
          </ElTableColumn>
        </ElTable>
        <p class="muted mb-0">{{ compare.disclaimer }}</p>
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
      description="请运行 python scripts/04_train_cluster.py && python scripts/09_cluster_compare.py"
    />
  </div>
</template>

<style scoped>
.segment-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space-3); }
.err-text {
  color: var(--color-danger);
  font-size: var(--font-size-xs);
}
</style>
