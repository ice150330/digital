<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import {
  COLOR_AXIS_LABEL,
  COLOR_PRIMARY,
  COLOR_SURFACE,
  COLOR_TEXT,
  COLOR_WARNING,
} from '../utils/chartTheme'

const props = defineProps<{
  total: number
  positiveRate: number
}>()

const option = computed(() => {
  const positive = Math.round(props.total * props.positiveRate)
  const negative = Math.max(0, props.total - positive)
  return {
    color: [COLOR_PRIMARY, COLOR_WARNING],
    tooltip: {
      trigger: 'item',
      formatter: (item: { name: string; value: number; percent: number }) =>
        `${item.name}<br/>${item.value.toLocaleString('zh-CN')}（${item.percent.toFixed(2)}%）`,
    },
    legend: {
      bottom: 0,
      icon: 'circle',
      textStyle: { color: COLOR_AXIS_LABEL },
    },
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '39%',
        style: {
          text: `${(props.positiveRate * 100).toFixed(2)}%`,
          fill: COLOR_TEXT,
          fontSize: 24,
          fontWeight: 600,
          textAlign: 'center',
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '51%',
        style: {
          text: '正类占比',
          fill: COLOR_AXIS_LABEL,
          fontSize: 12,
          textAlign: 'center',
        },
      },
    ],
    series: [
      {
        type: 'pie',
        radius: ['56%', '75%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        label: { show: false },
        itemStyle: { borderColor: COLOR_SURFACE, borderWidth: 3 },
        data: [
          { name: '转化', value: positive },
          { name: '未转化', value: negative },
        ],
      },
    ],
  }
})
</script>

<template>
  <BaseChart :option="option" height="var(--chart-height-md)" />
</template>
