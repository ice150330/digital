<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import {
  COLOR_AXIS_LABEL, COLOR_DANGER, COLOR_PRIMARY, COLOR_SPLIT_LINE,
} from '../utils/chartTheme'

const props = defineProps<{
  feature: string
  grid: number[]
  proba: number[]
  baseValue: number
  baseProba: number
  targetProba?: number
}>()

const option = computed(() => ({
  grid: { left: 56, right: 24, top: 24, bottom: 32 },
  tooltip: {
    trigger: 'axis',
    valueFormatter: (v: number) => Number(v).toFixed(4),
  },
  xAxis: {
    type: 'value', name: props.feature, nameLocation: 'middle', nameGap: 24,
    min: props.grid[0], max: props.grid[props.grid.length - 1],
    axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
  },
  yAxis: {
    type: 'value', name: 'proba', min: 0, max: 1,
    axisLabel: { color: COLOR_AXIS_LABEL }, splitLine: { lineStyle: { color: COLOR_SPLIT_LINE } },
  },
  series: [
    {
      name: 'proba', type: 'line', showSymbol: false, smooth: true,
      data: props.grid.map((g, i) => [g, props.proba[i]]),
      lineStyle: { width: 2.5, color: COLOR_PRIMARY }, itemStyle: { color: COLOR_PRIMARY },
      markLine: {
        symbol: 'none',
        data: [
          ...(props.targetProba != null
            ? [{
                yAxis: props.targetProba,
                label: { formatter: `目标 ${props.targetProba}`, color: COLOR_DANGER, fontSize: 10 },
                lineStyle: { color: COLOR_DANGER, type: 'dashed', width: 1.2 },
              }]
            : []),
          {
            xAxis: props.baseValue,
            label: { formatter: '当前值', color: COLOR_AXIS_LABEL, fontSize: 10 },
            lineStyle: { color: COLOR_AXIS_LABEL, type: 'dotted', width: 1.2 },
          },
        ],
      },
    },
    {
      name: '当前样本', type: 'scatter',
      data: [[props.baseValue, props.baseProba]],
      symbolSize: 10, itemStyle: { color: COLOR_DANGER },
    },
  ],
}))
</script>

<template>
  <BaseChart :option="option" />
</template>
