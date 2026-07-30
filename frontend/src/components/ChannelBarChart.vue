<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  channels: Array<{ channel?: string; n?: number; conversion_rate?: number }>
}>()

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!el.value) return
  if (!chart) chart = echarts.init(el.value)
  const names = props.channels.map((c) => String(c.channel ?? '—'))
  const rates = props.channels.map((c) => Number(c.conversion_rate ?? 0) * 100)
  chart.setOption(
    {
      grid: { left: 48, right: 16, top: 24, bottom: 40 },
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v: number) => `${Number(v).toFixed(2)}%`,
      },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: { color: '#909399', fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        name: '转化率%',
        axisLabel: { color: '#909399' },
        splitLine: { lineStyle: { color: '#ebeef5' } },
      },
      series: [
        {
          type: 'bar',
          data: rates,
          itemStyle: { color: '#409eff' },
          barMaxWidth: 36,
        },
      ],
    },
    true,
  )
}

function onResize() {
  chart?.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
watch(() => props.channels, () => render(), { deep: true })
</script>

<template>
  <div ref="el" class="chart" />
</template>

<style scoped>
.chart {
  width: 100%;
  height: var(--chart-height);
}
</style>
