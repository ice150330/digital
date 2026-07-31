<script setup lang="ts">
/**
 * 图表生命周期通用封装（Stage 2）：init / ResizeObserver / dispose / watch。
 * 业务图表组件只需 computed option 后 <BaseChart :option="option" />，
 * 不再各自复制 init/resize 样板；容器尺寸变化（含侧栏折叠）自动 resize。
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { EChartsCoreOption } from 'echarts/core'
import echarts from '../utils/echarts'

const props = withDefaults(
  defineProps<{
    option: EChartsCoreOption
    /** 容器高度；默认取 token --chart-height，大屏传具体值 */
    height?: string
    /** 主题作用域标记（色值由 option 携带，此处仅作 data 属性供 CSS） */
    theme?: 'default' | 'screen'
    notMerge?: boolean
  }>(),
  {
    height: 'var(--chart-height)',
    theme: 'default',
    notMerge: true,
  },
)

const el = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let observer: ResizeObserver | null = null

function render() {
  if (!el.value || el.value.clientHeight === 0) return
  if (!chart) chart = echarts.init(el.value)
  chart.setOption(props.option, props.notMerge)
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  render()
  if (el.value && typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(() => resize())
    observer.observe(el.value)
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
  chart?.dispose()
  chart = null
})

watch(() => props.option, render, { deep: true })

defineExpose({ resize })
</script>

<template>
  <div ref="el" class="base-chart" :data-theme="theme" :style="{ height }" />
</template>

<style scoped>
.base-chart {
  width: 100%;
}
</style>
