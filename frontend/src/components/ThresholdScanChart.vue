<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import type { ThresholdScanRow } from '../api/models'
import {
  COLOR_DANGER, COLOR_INFO, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING,
  COLOR_AXIS_LABEL, COLOR_SPLIT_LINE,
} from '../utils/chartTheme'

const props = defineProps<{
  rows: ThresholdScanRow[]
  currentThreshold?: number
  bestCostThreshold?: number
  selectedThreshold?: number
  costFn?: number
  costFp?: number
  title?: string
}>()

const option = computed(() => {
  const markLines: Array<Record<string, unknown>> = []
  if (props.currentThreshold != null) {
    markLines.push({
      xAxis: props.currentThreshold,
      label: { formatter: `当前 ${props.currentThreshold}`, color: COLOR_PRIMARY, fontSize: 10 },
      lineStyle: { color: COLOR_PRIMARY, type: 'solid', width: 1.5 },
    })
  }
  if (props.bestCostThreshold != null) {
    markLines.push({
      xAxis: props.bestCostThreshold,
      label: { formatter: `成本最优 ${props.bestCostThreshold}`, color: COLOR_WARNING, fontSize: 10 },
      lineStyle: { color: COLOR_WARNING, type: 'dashed', width: 1.5 },
    })
  }
  if (props.selectedThreshold != null) {
    markLines.push({
      xAxis: props.selectedThreshold,
      label: { formatter: `选中 ${props.selectedThreshold}`, color: COLOR_DANGER, fontSize: 10 },
      lineStyle: { color: COLOR_DANGER, type: 'dotted', width: 1.5 },
    })
  }
  const xs = props.rows.map((r) => r.threshold)
  return {
    legend: { top: 0, textStyle: { color: COLOR_AXIS_LABEL, fontSize: 11 } },
    grid: { left: 48, right: 56, top: 36, bottom: 28 },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => Number(v).toFixed(4) },
    xAxis: {
      type: 'value', name: '阈值', nameLocation: 'middle', nameGap: 22,
      min: xs[0] ?? 0, max: xs[xs.length - 1] ?? 1,
      axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
    },
    yAxis: [
      {
        type: 'value', name: '指标', min: 0, max: 1,
        axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
      },
      {
        type: 'value', name: '期望成本', min: 0,
        axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'Precision', type: 'line', showSymbol: false,
        data: props.rows.map((r) => [r.threshold, r.precision]),
        lineStyle: { width: 2, color: COLOR_PRIMARY }, itemStyle: { color: COLOR_PRIMARY },
        markLine: { symbol: 'none', data: markLines },
      },
      {
        name: 'Recall', type: 'line', showSymbol: false,
        data: props.rows.map((r) => [r.threshold, r.recall]),
        lineStyle: { width: 2, color: COLOR_SUCCESS }, itemStyle: { color: COLOR_SUCCESS },
      },
      {
        name: 'F1', type: 'line', showSymbol: false,
        data: props.rows.map((r) => [r.threshold, r.f1]),
        lineStyle: { width: 2, color: COLOR_INFO }, itemStyle: { color: COLOR_INFO },
      },
      {
        name: `期望成本（右轴 FP×${props.costFp ?? 1}+FN×${props.costFn ?? 5}）`,
        type: 'line', yAxisIndex: 1, showSymbol: false,
        data: props.rows.map((r) => [r.threshold, r.expected_cost]),
        lineStyle: { width: 2, type: 'dashed', color: COLOR_DANGER }, itemStyle: { color: COLOR_DANGER },
      },
    ],
  }
})
</script>

<template>
  <div>
    <div v-if="title" class="title">{{ title }}</div>
    <BaseChart :option="option" height="320px" />
  </div>
</template>

<style scoped>
.title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
</style>
