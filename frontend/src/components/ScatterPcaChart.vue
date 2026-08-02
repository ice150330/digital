<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { clusterColor, COLOR_AXIS_LABEL, COLOR_SPLIT_LINE } from '../utils/chartTheme'

interface PcaPoint { x: number; y: number; cluster: number; customer_id?: number }

const props = defineProps<{
  points: PcaPoint[]
  autoNames?: Record<string, string>
  title?: string
}>()

const option = computed(() => {
  const clusters = [...new Set(props.points.map((p) => p.cluster))].sort((a, b) => a - b)
  return {
    legend: { top: 0, textStyle: { color: COLOR_AXIS_LABEL, fontSize: 11 } },
    grid: { left: 48, right: 24, top: 36, bottom: 32 },
    tooltip: {
      formatter: (p: { seriesName: string; data: [number, number]; dataIndex: number; seriesIndex: number }) => {
        const pts = props.points.filter((pt) => pt.cluster === clusters[p.seriesIndex])
        const pt = pts[p.dataIndex]
        const cid = pt?.customer_id != null ? `<br/>CustomerID ${pt.customer_id}` : ''
        return `${p.seriesName}<br/>(${p.data[0].toFixed(2)}, ${p.data[1].toFixed(2)})${cid}`
      },
    },
    xAxis: {
      type: 'value', name: 'PC1', nameLocation: 'middle', nameGap: 22,
      axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    yAxis: {
      type: 'value', name: 'PC2',
      axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    series: clusters.map((c) => ({
      name: props.autoNames?.[String(c)] ? `簇${c} ${props.autoNames[String(c)]}` : `簇${c}`,
      type: 'scatter',
      data: props.points.filter((p) => p.cluster === c).map((p) => [p.x, p.y]),
      symbolSize: 6,
      itemStyle: { color: clusterColor(c), opacity: 0.75 },
    })),
  }
})
</script>

<template>
  <div>
    <div v-if="title" class="title">{{ title }}</div>
    <BaseChart :option="option" height="var(--chart-height-lg)" />
  </div>
</template>

<style scoped>
.title { margin-bottom: var(--space-2); font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); }
</style>
