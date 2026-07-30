<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, MarkLineComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { BudgetCurvePoint } from '../api/simulate'
import {
  COLOR_AXIS_LABEL, COLOR_DANGER, COLOR_INFO, COLOR_PRIMARY, COLOR_SPLIT_LINE, COLOR_SUCCESS,
} from '../utils/chartTheme'

echarts.use([LineChart, GridComponent, LegendComponent, MarkLineComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  points: BudgetCurvePoint[]
  recommendedK?: number
  budget?: number | null
  title?: string
}>()

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const option = computed(() => {
  const markLines: Array<Record<string, unknown>> = []
  if (props.recommendedK != null && props.recommendedK > 0) {
    markLines.push({
      xAxis: props.recommendedK,
      label: { formatter: `推荐 K=${props.recommendedK}`, color: COLOR_DANGER, fontSize: 10 },
      lineStyle: { color: COLOR_DANGER, type: 'dashed', width: 1.5 },
    })
  }
  if (props.budget != null && props.budget > 0) {
    markLines.push({
      xAxis: props.budget,
      label: { formatter: `预算 ${props.budget}`, color: COLOR_INFO, fontSize: 10 },
      lineStyle: { color: COLOR_INFO, type: 'dotted', width: 1.5 },
    })
  }
  return {
    legend: { top: 0, textStyle: { color: COLOR_AXIS_LABEL, fontSize: 11 } },
    grid: { left: 56, right: 56, top: 36, bottom: 28 },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => Number(v).toFixed(2) },
    xAxis: {
      type: 'value', name: '触达人数 K', nameLocation: 'middle', nameGap: 22,
      axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    yAxis: [
      {
        type: 'value', name: '期望金额',
        axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
      },
      {
        type: 'value', name: '期望转化数', min: 0,
        axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '期望净收益', type: 'line', showSymbol: false,
        data: props.points.map((p) => [p.k, p.expected_net]),
        lineStyle: { width: 2.5, color: COLOR_PRIMARY }, itemStyle: { color: COLOR_PRIMARY },
        areaStyle: { color: COLOR_PRIMARY, opacity: 0.08 },
        markLine: { symbol: 'none', data: markLines },
      },
      {
        name: '期望毛收益', type: 'line', showSymbol: false,
        data: props.points.map((p) => [p.k, p.expected_revenue]),
        lineStyle: { width: 1.5, type: 'dashed', color: COLOR_SUCCESS }, itemStyle: { color: COLOR_SUCCESS },
      },
      {
        name: '期望转化数（右轴）', type: 'line', yAxisIndex: 1, showSymbol: false,
        data: props.points.map((p) => [p.k, p.expected_conversions]),
        lineStyle: { width: 1.5, type: 'dotted', color: COLOR_INFO }, itemStyle: { color: COLOR_INFO },
      },
    ],
  }
})

function render() {
  if (!el.value) return
  if (!chart) chart = echarts.init(el.value)
  chart.setOption(option.value, true)
}
function onResize() { chart?.resize() }
onMounted(() => { render(); window.addEventListener('resize', onResize) })
onUnmounted(() => { window.removeEventListener('resize', onResize); chart?.dispose(); chart = null })
watch(() => [props.points, props.recommendedK], render, { deep: true })
</script>

<template>
  <div>
    <div v-if="title" class="title">{{ title }}</div>
    <div ref="el" class="chart" />
  </div>
</template>

<style scoped>
.title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.chart { width: 100%; height: 320px; }
</style>
