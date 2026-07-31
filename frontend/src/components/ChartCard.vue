<script setup lang="ts">
/**
 * chart-spec v1.0 → ECharts option 映射器（Stage 4）。
 * 后端 render_chart 工具产出纯 JSON spec（宿主计算真实数据），
 * 本组件按 chart_type 分派构造 option，色板走前端 chartTheme（单一真相），
 * caliber/disclaimer 渲染为卡片脚注；未知 chart_type 走兜底提示不崩。
 */
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { chartColors, axisTheme } from '../utils/chartTheme'

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

const props = defineProps<{ spec: ChartSpec }>()

const palette = chartColors()
const axis = axisTheme()

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

const supported = computed(() => ['bar', 'line', 'pie'].includes(props.spec.chart_type))

const option = computed(() => {
  const s = props.spec
  const fmt = formatter(s.value_format)
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
      <BaseChart :option="option" height="260px" />
      <div class="chart-card-foot">
        <span class="caliber">{{ spec.caliber }}</span>
        <span v-if="spec.disclaimer" class="disclaimer-inline">· {{ spec.disclaimer }}</span>
      </div>
    </template>
    <div v-else class="chart-card-unsupported">
      暂不支持在会话内渲染 chart_type=「{{ spec.chart_type }}」；请尝试 bar / line / pie。
    </div>
  </div>
</template>

<style scoped>
.chart-card {
  margin: var(--space-sm) 0;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}
.chart-card-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  margin-bottom: var(--space-xs);
}
.chart-card-foot {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.6;
}
.disclaimer-inline {
  color: var(--color-warning);
}
.chart-card-unsupported {
  padding: var(--space-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  text-align: center;
}
</style>
