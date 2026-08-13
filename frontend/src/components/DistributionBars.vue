<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { chartColors } from '../utils/chartTheme'
import type { HistBin } from '../api/data'

const props = withDefaults(defineProps<{
  bins: HistBin[]
  label?: string
  loading?: boolean
}>(), {
  loading: false,
})

const option = computed(() => {
  const colors = chartColors('default')
  const categories = props.bins.map((b) => `${b.lo}-${b.hi}`)
  const values = props.bins.map((b) => b.count)
  return {
    color: colors,
    grid: { left: '12%', right: '8%', top: '16%', bottom: '16%' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        const bin = props.bins[p.dataIndex]
        return `${props.label || '分布'} <br />区间 ${bin.lo}-${bin.hi}：${bin.count} 条`
      },
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { rotate: categories.length > 6 ? 30 : 0, fontSize: 11 },
    },
    yAxis: { type: 'value', name: '计数' },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { borderRadius: [4, 4, 0, 0], color: colors[0] },
      barWidth: '60%',
    }],
  }
})
</script>

<template>
  <div class="distribution-bars">
    <BaseChart :option="option" height="var(--chart-height-sm)" />
  </div>
</template>

<style scoped>
.distribution-bars { width: 100%; }
</style>
