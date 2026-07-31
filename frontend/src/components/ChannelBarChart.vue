<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { COLOR_PRIMARY, axisTheme } from '../utils/chartTheme'

const props = defineProps<{
  channels: Array<{ channel?: string; n?: number; conversion_rate?: number }>
}>()

const axis = axisTheme()

const option = computed(() => {
  const names = props.channels.map((c) => String(c.channel ?? '—'))
  const rates = props.channels.map((c) => Number(c.conversion_rate ?? 0) * 100)
  return {
    grid: { left: 48, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (v: number) => `${Number(v).toFixed(2)}%`,
    },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: axis.axisLabel, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '转化率%',
      axisLabel: { color: axis.axisLabel },
      splitLine: { lineStyle: { color: axis.splitLine } },
    },
    series: [
      {
        type: 'bar',
        data: rates,
        itemStyle: { color: COLOR_PRIMARY },
        barMaxWidth: 36,
      },
    ],
  }
})
</script>

<template>
  <BaseChart :option="option" />
</template>
