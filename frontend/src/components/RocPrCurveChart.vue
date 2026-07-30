<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { COLOR_PRIMARY, COLOR_SUCCESS, COLOR_INFO, COLOR_AXIS_LABEL, COLOR_SPLIT_LINE } from '../utils/chartTheme'

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  pr: { precision: number[]; recall: number[] }
  roc: { fpr: number[]; tpr: number[] }
  prAuc?: number
  rocAuc?: number
  title?: string
}>()

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const option = computed(() => ({
  legend: { top: 0, textStyle: { color: COLOR_AXIS_LABEL, fontSize: 11 } },
  grid: [
    { left: 48, right: '56%', top: 36, bottom: 32 },
    { left: '52%', right: 16, top: 36, bottom: 32 },
  ],
  tooltip: { trigger: 'axis', valueFormatter: (v: number) => Number(v).toFixed(4) },
  xAxis: [
    {
      gridIndex: 0, type: 'value', name: 'Recall', nameLocation: 'middle', nameGap: 22,
      min: 0, max: 1, axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    {
      gridIndex: 1, type: 'value', name: 'FPR', nameLocation: 'middle', nameGap: 22,
      min: 0, max: 1, axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
  ],
  yAxis: [
    {
      gridIndex: 0, type: 'value', name: 'Precision', min: 0, max: 1,
      axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    {
      gridIndex: 1, type: 'value', name: 'TPR', min: 0, max: 1,
      axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
  ],
  series: [
    {
      name: `PR（AUC=${props.prAuc?.toFixed(4) ?? '-'}）`,
      type: 'line', xAxisIndex: 0, yAxisIndex: 0,
      data: props.pr.recall.map((r, i) => [r, props.pr.precision[i]]),
      showSymbol: false, lineStyle: { width: 2, color: COLOR_PRIMARY },
      itemStyle: { color: COLOR_PRIMARY },
    },
    {
      name: `ROC（AUC=${props.rocAuc?.toFixed(4) ?? '-'}）`,
      type: 'line', xAxisIndex: 1, yAxisIndex: 1,
      data: props.roc.fpr.map((f, i) => [f, props.roc.tpr[i]]),
      showSymbol: false, lineStyle: { width: 2, color: COLOR_SUCCESS },
      itemStyle: { color: COLOR_SUCCESS },
    },
    {
      name: '随机基线',
      type: 'line', xAxisIndex: 1, yAxisIndex: 1,
      data: [[0, 0], [1, 1]],
      showSymbol: false, lineStyle: { width: 1, type: 'dashed', color: COLOR_INFO },
      itemStyle: { color: COLOR_INFO },
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
watch(() => [props.pr, props.roc], render, { deep: true })
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
