<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { COLOR_PRIMARY, COLOR_TEXT } from '../utils/chartTheme'

echarts.use([HeatmapChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps<{
  confusion: { tn: number; fp: number; fn: number; tp: number }
  title?: string
}>()

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const option = computed(() => {
  const c = props.confusion
  const max = Math.max(c.tn, c.fp, c.fn, c.tp, 1)
  // x=预测, y=实际
  const data = [
    [0, 0, c.tn], [1, 0, c.fn],
    [0, 1, c.fp], [1, 1, c.tp],
  ]
  return {
    grid: { left: 80, right: 60, top: 16, bottom: 40 },
    tooltip: {
      formatter: (p: { data: [number, number, number] }) =>
        `实际${p.data[1] ? '正' : '负'} → 预测${p.data[0] ? '正' : '负'}：${p.data[2]}`,
    },
    xAxis: {
      type: 'category', data: ['预测负', '预测正'],
      axisLabel: { color: COLOR_TEXT }, splitArea: { show: true },
    },
    yAxis: {
      type: 'category', data: ['实际负', '实际正'],
      axisLabel: { color: COLOR_TEXT }, splitArea: { show: true },
    },
    visualMap: {
      min: 0, max, calculable: true, orient: 'vertical', right: 0, top: 'center',
      inRange: { color: ['#f2f6fc', COLOR_PRIMARY] },
      textStyle: { color: COLOR_TEXT, fontSize: 10 },
    },
    series: [
      {
        type: 'heatmap',
        data,
        label: { show: true, color: COLOR_TEXT, fontWeight: 600 },
        itemStyle: { borderColor: '#fff', borderWidth: 2 },
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
watch(() => props.confusion, render, { deep: true })
</script>

<template>
  <div>
    <div v-if="title" class="title">{{ title }}</div>
    <div ref="el" class="chart" />
  </div>
</template>

<style scoped>
.title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.chart { width: 100%; height: 240px; }
</style>
