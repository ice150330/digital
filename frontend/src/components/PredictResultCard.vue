<script setup lang="ts">
import { computed } from 'vue'
import type { PredictData } from '../api/models'
import { formatProba } from '../utils/format'
import Icon from './Icon.vue'
import RunIdChip from './RunIdChip.vue'
import Tag from './Tag.vue'

const props = defineProps<{ result: PredictData }>()
const percent = computed(() => Math.max(0, Math.min(100, props.result.proba * 100)))
</script>

<template>
  <article class="predict-card">
    <header>
      <div class="predict-title"><span><Icon icon="uil:percentage" size="md" /></span><div><strong>预测结果</strong><small>{{ result.model_name }}</small></div></div>
      <Tag :tone="result.label === 1 ? 'success' : 'neutral'" size="md">{{ result.label === 1 ? '预测转化' : '预测未转化' }}</Tag>
    </header>
    <div class="probability"><span>转化概率</span><strong>{{ formatProba(result.proba) }}</strong></div>
    <div class="probability-rail" aria-hidden="true"><span :style="{ width: `${percent}%` }" /></div>
    <div class="probability-scale"><span>0</span><span>阈值 {{ formatProba(result.threshold) }}</span><span>1</span></div>
    <footer>
      <RunIdChip :value="result.run_id" />
      <span v-if="result.customer_id != null" class="customer-id">CustomerID {{ result.customer_id }}</span>
    </footer>
  </article>
</template>

<style scoped>
.predict-card { padding: var(--space-5); border: 1px solid var(--color-primary-100); border-radius: var(--radius-card); background: var(--bg-card); box-shadow: var(--shadow-sm); }
.predict-card header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.predict-title { display: flex; align-items: center; gap: var(--space-3); }
.predict-title > span { display: grid; width: var(--space-8); height: var(--space-8); place-items: center; border-radius: var(--radius-lg); background: var(--color-primary-50); color: var(--color-primary-600); }
.predict-title strong, .predict-title small { display: block; }
.predict-title strong { color: var(--text-title); font-size: var(--font-size-md); }
.predict-title small { margin-top: var(--space-1); color: var(--text-secondary); font-size: var(--font-size-xs); }
.probability { display: flex; align-items: end; justify-content: space-between; margin-top: var(--space-5); }
.probability span { color: var(--text-secondary); font-size: var(--font-size-sm); }
.probability strong { color: var(--color-primary-700); font-family: var(--font-family-number); font-size: var(--font-size-3xl); }
.probability-rail { height: var(--space-2); margin-top: var(--space-3); overflow: hidden; border-radius: var(--radius-full); background: var(--bg-subtle); }
.probability-rail span { display: block; height: 100%; border-radius: inherit; background: var(--color-primary-500); transition: width var(--motion-duration-base) var(--motion-easing-out); }
.probability-scale { display: flex; justify-content: space-between; margin-top: var(--space-1); color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
.predict-card footer { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-top: var(--space-4); }
.customer-id { color: var(--text-secondary); font-family: var(--font-family-number); font-size: var(--font-size-xs); }
</style>
