<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { LiftDecile } from '../api/models'
import { COLOR_PRIMARY, COLOR_WARNING, COLOR_AXIS_LABEL, COLOR_SPLIT_LINE } from '../utils/chartTheme'

echarts.use([BarChart, LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  deciles: LiftDecile[]
  title?: string
}>()

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const option = computed(() => ({
  legend: { top: 0, textStyle: { color: COLOR_AXIS_LABEL, fontSize: 11 } },
  grid: { left: 48, right: 48, top: 36, bottom: 28 },
  tooltip: {
    trigger: 'axis',
    formatter: (ps: Array<{ axisValue: string; seriesName: string; data: number }>) => {
      const d = props.deciles[Number(ps[0].axisValue) - 1]
      if (!d) return ''
      return (
        `第 ${d.decile} 十分位<br/>人数 ${d.n}（正类 ${d.positives}）<br/>` +
        `累计捕获率 ${(d.capture_rate * 100).toFixed(2)}%<br/>lift ${d.lift.toFixed(3)}`
      )
    },
  },
  xAxis: {
    type: 'category',
    data: props.deciles.map((d) => String(d.decile)),
    name: '十分位（按预测概率降序）',
    nameLocation: 'middle', nameGap: 24,
    axisLabel: { color: COLOR_AXIS_LABEL },
  },
  yAxis: [
    {
      type: 'value', name: '累计捕获率', min: 0, max: 1,
      axisLabel: { color: COLOR_AXIS_LABEL, formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
      splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    {
      type: 'value', name: 'lift（倍数）', min: 0,
      axisLabel: { color: COLOR_AXIS_LABEL },
      splitLine: { show: false },
    },
  ],
  series: [
    {
      name: '累计捕获率',
      type: 'bar',
      data: props.deciles.map((d) => Number(d.capture_rate.toFixed(4))),
      itemStyle: { color: COLOR_PRIMARY, borderRadius: [3, 3, 0, 0] },
      barMaxWidth: 28,
    },
    {
      name: 'lift（右轴，相对全量基准的倍数）',
      type: 'line', yAxisIndex: 1,
      data: props.deciles.map((d) => Number(d.lift.toFixed(4))),
      lineStyle: { width: 2, color: COLOR_WARNING }, itemStyle: { color: COLOR_WARNING },
    },
  ],
}))

function render() {
  if (!el.value) return
  if (!chart) chart = echarts.init(el.value)
  chart.setOption(option.value, true)
}
function onResize() { chart?.resize() }
onMounted(() => { render(); window.addEventListener('resize', onResize) })
onUnmounted(() => { window.removeEventListener('resize', onResize); chart?.dispose(); chart = null })
watch(() => props.deciles, render, { deep: true })
</script>

<template>
  <div>
    <div v-if="title" class="title">{{ title }}</div>
    <div ref="el" class="chart" />
  </div>
</template>

<style scoped>
.title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.chart { width: 100%; height: var(--chart-height); }
</style>
