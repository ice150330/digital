<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { COLOR_SHAP_POS, COLOR_SHAP_NEG, COLOR_TEXT, axisTheme } from '../utils/chartTheme'

export interface ShapItem {
  name: string
  value: number
}

const props = defineProps<{
  items: ShapItem[]
}>()

const axis = axisTheme()

const option = computed(() => {
  const rows = [...props.items].slice(0, 12).reverse()
  const names = rows.map((r) => r.name)
  const vals = rows.map((r) => r.value)
  return {
    grid: { left: 140, right: 24, top: 16, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (v: number) => Number(v).toFixed(4),
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: axis.axisLabel },
      splitLine: { lineStyle: { color: axis.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        color: COLOR_TEXT,
        width: 120,
        overflow: 'truncate',
        fontSize: 11,
      },
    },
    series: [
      {
        type: 'bar',
        data: vals.map((v) => ({
          value: v,
          itemStyle: {
            color: v >= 0 ? COLOR_SHAP_POS : COLOR_SHAP_NEG,
          },
        })),
        barMaxWidth: 18,
      },
    ],
  }
})
</script>

<template>
  <div>
    <BaseChart :option="option" />
    <p class="legend muted">蓝 = 推向转化 · 红 = 拉低转化（贡献方向，非严格因果）</p>
  </div>
</template>

<style scoped>
.legend {
  margin: var(--space-1) 0 0;
}
</style>
