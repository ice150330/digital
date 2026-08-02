<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { COLOR_PRIMARY, COLOR_SUCCESS, COLOR_INFO, COLOR_AXIS_LABEL, COLOR_SPLIT_LINE } from '../utils/chartTheme'

const props = defineProps<{
  pr: { precision: number[]; recall: number[] }
  roc: { fpr: number[]; tpr: number[] }
  prAuc?: number
  rocAuc?: number
  title?: string
}>()

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
</script>

<template>
  <div>
    <div v-if="title" class="title">{{ title }}</div>
    <BaseChart :option="option" />
  </div>
</template>

<style scoped>
.title { margin-bottom: var(--space-2); font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); }
</style>
