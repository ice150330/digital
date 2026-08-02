<script setup lang="ts">
import { computed } from 'vue'
import type { ClusterRow } from '../api/segments'
import Icon from './Icon.vue'
import Tag from './Tag.vue'
import { formatInt, formatPercent } from '../utils/format'

const props = defineProps<{
  cluster: ClusterRow
  name?: string
  stability?: number | null
}>()

const topFeatures = computed(() => Object.entries(props.cluster.profile_means || {})
  .filter(([, value]) => value != null && Number.isFinite(Number(value)))
  .slice(0, 3)
  .map(([name, value]) => ({ name, value: Number(value) })))

const stabilityTone = computed(() => {
  const value = props.stability
  if (value == null) return 'neutral'
  if (value >= 0.75) return 'success'
  if (value >= 0.5) return 'primary'
  return 'warning'
})
</script>

<template>
  <article class="segment-card">
    <header>
      <div class="segment-identity">
        <span class="segment-icon"><Icon icon="uil:users-alt" size="md" /></span>
        <div><strong>{{ name || `簇 ${cluster.cluster_id}` }}</strong><span>cluster_id={{ cluster.cluster_id }}</span></div>
      </div>
      <Tag v-if="stability != null" :tone="stabilityTone">ARI {{ stability.toFixed(3) }}</Tag>
    </header>
    <div class="segment-stats">
      <div><span>人数</span><strong>{{ formatInt(cluster.n) }}</strong></div>
      <div><span>占比</span><strong>{{ formatPercent(cluster.share) }}</strong></div>
      <div><span>事后转化</span><strong>{{ formatPercent(cluster.conversion_rate) }}</strong></div>
    </div>
    <div v-if="topFeatures.length" class="feature-list">
      <span v-for="feature in topFeatures" :key="feature.name">
        {{ feature.name }} <strong>{{ feature.value.toFixed(1) }}</strong>
      </span>
    </div>
    <p>{{ cluster.conversion_note || '画像均值用于描述当前簇，不代表因果效果。' }}</p>
  </article>
</template>

<style scoped>
.segment-card { padding: var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-card); box-shadow: var(--shadow-xs); }
.segment-card header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.segment-identity { display: flex; align-items: center; gap: var(--space-3); min-width: 0; }
.segment-icon { display: grid; width: var(--space-8); height: var(--space-8); flex: 0 0 auto; place-items: center; border-radius: var(--radius-lg); background: var(--color-primary-50); color: var(--color-primary-600); }
.segment-identity strong { display: block; overflow: hidden; color: var(--text-title); font-size: var(--font-size-sm); text-overflow: ellipsis; white-space: nowrap; }
.segment-identity span { display: block; margin-top: var(--space-1); color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
.segment-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-2); margin-top: var(--space-4); }
.segment-stats div { padding: var(--space-2); border-radius: var(--radius-md); background: var(--bg-subtle); }
.segment-stats span, .segment-stats strong { display: block; }
.segment-stats span { color: var(--text-secondary); font-size: var(--font-size-xs); }
.segment-stats strong { margin-top: var(--space-1); color: var(--text-title); font-family: var(--font-family-number); font-size: var(--font-size-md); }
.feature-list { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-3); }
.feature-list span { padding: var(--space-1) var(--space-2); border: 1px solid var(--border-default); border-radius: var(--radius-full); color: var(--text-secondary); font-size: var(--font-size-xs); }
.feature-list strong { color: var(--text-title); font-family: var(--font-family-number); }
.segment-card p { margin: var(--space-3) 0 0; color: var(--text-secondary); font-size: var(--font-size-xs); line-height: 1.6; }
</style>
