<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { COLOR_PRIMARY, COLOR_AXIS_LABEL, COLOR_SPLIT_LINE } from '../utils/chartTheme'

const props = defineProps<{
  feature: string
  grid: number[]
  pdp: number[]
  ice?: Array<{ index: number; values: number[] }>
  loading?: boolean
}>()

const option = computed(() => {
  const iceOpacity = 0.12
  const iceWidth = 1
  const pdpWidth = 3
  const iceSeries = (props.ice ?? []).slice(0, 50).map((line) => ({
    type: 'line',
    data: line.values.map((v, i) => [props.grid[i], v]),
    symbol: 'none',
    lineStyle: { width: iceWidth, opacity: iceOpacity, color: COLOR_PRIMARY },
    silent: true,
    z: 1,
    tooltip: { show: false },
  }))

  return {
    color: [COLOR_PRIMARY],
    grid: { left: '10%', right: '8%', top: '12%', bottom: '16%' },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params.find((x) => x.seriesType === 'line' && x.seriesName === 'PDP') : params
        if (!p) return ''
        return `${props.feature} = ${p.data[0]}<br />平均预测概率 ${(p.data[1] * 100).toFixed(2)}%`
      },
    },
    xAxis: {
      type: 'value',
      name: props.feature,
      axisLabel: { color: COLOR_AXIS_LABEL },
      splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    yAxis: {
      type: 'value',
      name: '预测概率',
      axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(0)}%`, color: COLOR_AXIS_LABEL },
      splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    series: [
      ...iceSeries,
      {
        name: 'PDP',
        type: 'line',
        data: props.pdp.map((v, i) => [props.grid[i], v]),
        symbol: 'none',
        lineStyle: { width: pdpWidth, color: COLOR_PRIMARY },
        z: 2,
      },
    ],
  }
})
</script>

<template>
  <div class="pdp-ice-chart">
    <BaseChart :option="option" height="var(--chart-height-md)" />
  </div>
</template>

<style scoped>
.pdp-ice-chart { width: 100%; }
</style>
