<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { COLOR_HEAT_LOW, COLOR_PRIMARY, COLOR_SURFACE } from '../utils/chartTheme'
import type { CrossMatrixData } from '../api/data'

const props = defineProps<{
  data: CrossMatrixData
  loading?: boolean
}>()

const rows = computed(() => [...new Set(props.data.cells.map((c) => c.row))])
const cols = computed(() => [...new Set(props.data.cells.map((c) => c.col))])

const heatmapData = computed(() => {
  const rowIndex = Object.fromEntries(rows.value.map((r, i) => [r, i]))
  const colIndex = Object.fromEntries(cols.value.map((c, i) => [c, i]))
  return props.data.cells.map((c) => [rowIndex[c.row], colIndex[c.col], Number(c.conversion_rate.toFixed(4)), c.n])
})

const option = computed(() => {
  return {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const cell = props.data.cells[params.dataIndex]
        return `${cell.row} × ${cell.col}<br />样本 ${cell.n} · 转化率 ${(cell.conversion_rate * 100).toFixed(2)}%`
      },
    },
    grid: { left: '22%', right: '8%', top: '8%', bottom: '16%' },
    xAxis: {
      type: 'category',
      data: cols.value,
      axisLabel: { rotate: cols.value.length > 4 ? 30 : 0, fontSize: 11 },
    },
    yAxis: {
      type: 'category',
      data: rows.value,
      axisLabel: { fontSize: 11 },
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: { color: [COLOR_HEAT_LOW, COLOR_SURFACE, COLOR_PRIMARY] },
      formatter: (value: number) => `${(value * 100).toFixed(0)}%`,
    },
    series: [{
      type: 'heatmap',
      data: heatmapData.value,
      label: {
        show: true,
        formatter: (p: any) => `${(p.data[2] * 100).toFixed(1)}%`,
        fontSize: 10,
      },
      emphasis: {
        itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.15)' },
      },
    }],
  }
})
</script>

<template>
  <div class="cross-matrix-heatmap">
    <BaseChart :option="option" height="var(--chart-height-md)" />
  </div>
</template>

<style scoped>
.cross-matrix-heatmap { width: 100%; }
</style>
