<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import type { CalibrationSide } from '../api/models'
import { COLOR_DANGER, COLOR_PRIMARY, COLOR_INFO, COLOR_AXIS_LABEL, COLOR_SPLIT_LINE } from '../utils/chartTheme'

const props = defineProps<{
  before: CalibrationSide
  after: CalibrationSide
  method?: string
}>()

const option = computed(() => ({
  legend: { top: 0, textStyle: { color: COLOR_AXIS_LABEL, fontSize: 11 } },
  grid: { left: 48, right: 24, top: 36, bottom: 32 },
  tooltip: {
    trigger: 'axis',
    valueFormatter: (v: number) => Number(v).toFixed(4),
  },
  xAxis: {
    type: 'value', name: '预测概率均值', nameLocation: 'middle', nameGap: 22,
    min: 0, max: 1, axisLabel: { color: COLOR_AXIS_LABEL },
    splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
  },
  yAxis: {
    type: 'value', name: '实际正类率', min: 0, max: 1,
    axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
  },
  series: [
    {
      name: '完美校准',
      type: 'line', data: [[0, 0], [1, 1]], showSymbol: false,
      lineStyle: { width: 1, type: 'dashed', color: COLOR_INFO }, itemStyle: { color: COLOR_INFO },
    },
    {
      name: `校准前（ECE=${props.before.ece.toFixed(4)}）`,
      type: 'line',
      data: props.before.bins.map((b) => [b.mean_pred, b.frac_pos]),
      lineStyle: { width: 2, color: COLOR_DANGER }, itemStyle: { color: COLOR_DANGER },
    },
    {
      name: `校准后 ${props.method ?? ''}（ECE=${props.after.ece.toFixed(4)}）`,
      type: 'line',
      data: props.after.bins.map((b) => [b.mean_pred, b.frac_pos]),
      lineStyle: { width: 2, color: COLOR_PRIMARY }, itemStyle: { color: COLOR_PRIMARY },
    },
  ],
}))
</script>

<template>
  <div>
    <BaseChart :option="option" />
  </div>
</template>

<style scoped>
</style>
