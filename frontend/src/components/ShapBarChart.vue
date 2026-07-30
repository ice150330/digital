<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

export interface ShapItem {
  name: string
  value: number
}

const props = defineProps<{
  items: ShapItem[]
  title?: string
}>()

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const option = computed(() => {
  const rows = [...props.items].slice(0, 12).reverse()
  const names = rows.map((r) => r.name)
  const vals = rows.map((r) => r.value)
  return {
    grid: { left: 140, right: 24, top: 16, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (v: number) => Number(v).toFixed(4),
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#909399' },
      splitLine: { lineStyle: { color: '#ebeef5' } },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        color: '#606266',
        width: 120,
        overflow: 'truncate',
        fontSize: 11,
      },
    },
    series: [
      {
        type: 'bar',
        data: vals.map((v) => ({
          value: v,
          itemStyle: {
            color: v >= 0 ? '#409eff' : '#f56c6c',
          },
        })),
        barMaxWidth: 18,
      },
    ],
  }
})

function render() {
  if (!el.value) return
  if (!chart) chart = echarts.init(el.value)
  chart.setOption(option.value, true)
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

watch(
  () => props.items,
  () => render(),
  { deep: true },
)
</script>

<template>
  <div>
    <div v-if="title" class="title">{{ title }}</div>
    <div ref="el" class="chart" />
    <p class="legend muted">蓝 = 推向转化 · 红 = 拉低转化（贡献方向，非严格因果）</p>
  </div>
</template>

<style scoped>
.title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}
.chart {
  width: 100%;
  height: var(--chart-height);
}
.legend {
  margin: 4px 0 0;
}
</style>
