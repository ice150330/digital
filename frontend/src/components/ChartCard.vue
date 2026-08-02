<script setup lang="ts">
/**
 * chart-spec v1.0 → ECharts option 映射器（Stage 4）。
 * 后端 render_chart 工具产出纯 JSON spec（宿主计算真实数据），
 * 本组件按 chart_type 分派构造 option，色板走前端 chartTheme（单一真相），
 * caliber/disclaimer 渲染为卡片脚注；未知 chart_type 走兜底提示不崩。
 */
import { computed, ref } from 'vue'
import BaseChart from './BaseChart.vue'
import Button from './Button.vue'
import { chartColors, axisTheme, COLOR_HEAT_LOW } from '../utils/chartTheme'

export interface ChartSpec {
  spec_version: string
  chart_type: string
  title: string
  categories: string[]
  series: Array<{ name: string; values: number[] }>
  value_format: string
  axis: { x_name?: string; y_name?: string }
  caliber: string
  source: { kind?: string; ref?: string; run_id?: string | null }
  disclaimer?: string | null
}

const props = withDefaults(defineProps<{ spec: ChartSpec; allowZoom?: boolean }>(), { allowZoom: false })
const emit = defineEmits<{ zoom: []; regenerate: [] }>()
const chartRef = ref<InstanceType<typeof BaseChart> | null>(null)
const zoomed = ref(false)

const palette = chartColors()
const axis = axisTheme()

function downloadChart() {
  const url = chartRef.value?.getDataURL?.()
  if (!url) return
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.spec.title || 'chart'}.png`
  link.click()
}

function formatter(fmt: string) {
  switch (fmt) {
    case 'percent2':
      return (v: number) => `${(Number(v) * 100).toFixed(2)}%`
    case 'float4':
      return (v: number) => Number(v).toFixed(4)
    case 'money':
      return (v: number) => `¥${Math.round(Number(v)).toLocaleString('zh-CN')}`
    default:
      return (v: number) => `${Math.round(Number(v)).toLocaleString('zh-CN')}`
  }
}

const supported = computed(() => ['bar', 'line', 'pie', 'scatter', 'heatmap', 'funnel'].includes(props.spec.chart_type))

const option = computed(() => {
  const s = props.spec
  const fmt = formatter(s.value_format)
  if (s.chart_type === 'funnel') {
    return {
      tooltip: { trigger: 'item', valueFormatter: fmt },
      series: [{ type: 'funnel', left: '8%', top: 10, bottom: 10, width: '84%', min: 0, max: Math.max(...(s.series[0]?.values || [1])), minSize: '10%', maxSize: '90%', sort: 'descending', gap: 4, label: { color: axis.textStyle, fontSize: 11 }, data: s.categories.map((name, index) => ({ name, value: s.series[0]?.values[index] || 0 })) }],
    }
  }
  if (s.chart_type === 'scatter') {
    return {
      tooltip: { trigger: 'item', valueFormatter: fmt },
      grid: { left: 48, right: 20, top: 14, bottom: 34 },
      xAxis: { type: 'category', data: s.categories, axisLabel: { color: axis.textStyle, fontSize: 10 } },
      yAxis: { type: 'value', name: s.axis.y_name, axisLabel: { color: axis.axisLabel, fontSize: 10 }, splitLine: { lineStyle: { color: axis.splitLine } } },
      series: s.series.map((sr, i) => ({ name: sr.name, type: 'scatter', data: sr.values.map((value, index) => [index, value]), itemStyle: { color: palette[i % palette.length] }, symbolSize: 9 })),
    }
  }
  if (s.chart_type === 'heatmap') {
    const data = s.series.flatMap((sr, row) => sr.values.map((value, column) => [column, row, value]))
    return {
      tooltip: { position: 'top', valueFormatter: fmt },
      grid: { left: 52, right: 18, top: 10, bottom: 42 },
      xAxis: { type: 'category', data: s.categories, axisLabel: { color: axis.textStyle, fontSize: 10, interval: 0 } },
      yAxis: { type: 'category', data: s.series.map((sr) => sr.name), axisLabel: { color: axis.textStyle, fontSize: 10 } },
      visualMap: { min: 0, max: Math.max(...(s.series.flatMap((sr) => sr.values)), 1), calculable: false, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: [COLOR_HEAT_LOW, palette[0]] } },
      series: [{ type: 'heatmap', data, label: { show: true, color: axis.textStyle, fontSize: 10 } }],
    }
  }
  if (s.chart_type === 'pie') {
    return {
      tooltip: { trigger: 'item', formatter: (p: { name: string; value: number; percent: number }) => `${p.name}: ${fmt(p.value)}（${p.percent.toFixed(1)}%）` },
      legend: { bottom: 0, textStyle: { color: axis.axisLabel, fontSize: 11 } },
      series: [
        {
          type: 'pie',
          radius: ['38%', '66%'],
          center: ['50%', '44%'],
          data: s.categories.map((c, i) => ({ name: c, value: s.series[0]?.values[i] ?? 0, itemStyle: { color: palette[i % palette.length] } })),
          label: { color: axis.textStyle, fontSize: 11 },
        },
      ],
    }
  }
  const horizontal = s.chart_type === 'bar' && s.categories.length > 6
  const catAxis = {
    type: 'category',
    data: s.categories,
    axisLabel: { color: axis.textStyle, fontSize: 11, interval: 0, rotate: horizontal ? 0 : (s.categories.length > 5 ? 20 : 0) },
    axisLine: { lineStyle: { color: axis.splitLine } },
    axisTick: { show: false },
    name: horizontal ? undefined : s.axis.x_name,
  }
  const valAxis = {
    type: 'value',
    name: horizontal ? s.axis.x_name : s.axis.y_name,
    axisLabel: { color: axis.axisLabel, fontSize: 10, formatter: s.value_format === 'percent2' ? (v: number) => `${(v * 100).toFixed(0)}%` : undefined },
    splitLine: { lineStyle: { color: axis.splitLine } },
  }
  return {
    legend: s.series.length > 1 ? { top: 0, textStyle: { color: axis.axisLabel, fontSize: 11 } } : undefined,
    grid: { left: horizontal ? 120 : 48, right: 20, top: s.series.length > 1 ? 30 : 14, bottom: horizontal ? 20 : 34 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: fmt },
    xAxis: horizontal ? valAxis : catAxis,
    yAxis: horizontal ? { ...catAxis, name: undefined } : valAxis,
    series: s.series.map((sr, i) => ({
      name: sr.name,
      type: s.chart_type === 'line' ? 'line' : 'bar',
      data: sr.values,
      itemStyle: { color: palette[i % palette.length], borderRadius: s.chart_type === 'bar' ? (horizontal ? [0, 3, 3, 0] : [3, 3, 0, 0]) : undefined },
      barMaxWidth: 22,
      showSymbol: s.chart_type === 'line' ? false : undefined,
      lineStyle: s.chart_type === 'line' ? { width: 2, color: palette[i % palette.length] } : undefined,
    })),
  }
})
</script>

<template>
  <div class="chart-card">
    <div class="chart-card-title">{{ spec.title }}</div>
    <template v-if="supported">
      <div class="chart-card-toolbar">
        <span class="chart-kind">{{ spec.chart_type }}</span>
        <div v-if="allowZoom" class="chart-actions">
          <Button variant="icon-only" size="sm" icon="uil:expand-arrows-alt" title="放大图表" aria-label="放大图表" @click="zoomed = true; emit('zoom')" />
          <Button variant="icon-only" size="sm" icon="uil:redo" title="重新生成图表" aria-label="重新生成图表" @click="emit('regenerate')" />
          <Button variant="icon-only" size="sm" icon="uil:download-alt" title="下载图表" aria-label="下载图表" @click="downloadChart" />
        </div>
      </div>
      <BaseChart ref="chartRef" :option="option" height="var(--chart-height-sm)" />
      <div class="chart-card-foot">
        <span class="caliber">{{ spec.caliber }}</span>
        <span v-if="spec.disclaimer" class="disclaimer-inline">· {{ spec.disclaimer }}</span>
      </div>
    </template>
    <div v-else class="chart-card-unsupported">
      暂不支持在会话内渲染 chart_type=「{{ spec.chart_type }}」。
    </div>
    <div v-if="zoomed" class="chart-modal" role="dialog" aria-modal="true" @click.self="zoomed = false">
      <div class="chart-modal-inner">
        <div class="chart-modal-head"><strong>{{ spec.title }}</strong><Button variant="icon-only" size="sm" icon="uil:times" title="关闭放大图表" aria-label="关闭放大图表" @click="zoomed = false" /></div>
        <BaseChart :option="option" height="var(--chart-height-modal)" />
        <p class="chart-modal-foot">{{ spec.caliber }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-card {
  position: relative;
  margin: var(--space-2) 0;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-default);
  border-left: var(--space-1) solid var(--color-primary-500);
  border-radius: var(--radius-card);
  background: var(--bg-card);
  box-shadow: var(--shadow-xs);
}
.chart-card-title {
  margin-bottom: var(--space-1);
  color: var(--text-title);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}
.chart-card-toolbar { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); margin-bottom: var(--space-2); }
.chart-kind { color: var(--text-secondary); font-family: var(--font-family-code); font-size: var(--font-size-xs); }
.chart-actions { display: flex; gap: var(--space-1); }
.chart-card-foot {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  line-height: 1.6;
}
.disclaimer-inline {
  color: var(--color-warning-text);
}
.chart-card-unsupported {
  padding: var(--space-4);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  text-align: center;
}
.chart-modal { position: fixed; z-index: var(--z-modal); inset: 0; display: grid; place-items: center; padding: var(--space-6); background: rgb(15 23 42 / 42%); }
.chart-modal-inner { width: min(960px, 100%); padding: var(--space-5); border-radius: var(--radius-card); background: var(--bg-card); box-shadow: var(--shadow-lg); }
.chart-modal-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); color: var(--text-title); font-size: var(--font-size-lg); }
.chart-modal-foot { margin: 0; color: var(--text-secondary); font-size: var(--font-size-xs); }
</style>
