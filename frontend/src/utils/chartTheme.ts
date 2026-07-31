/**
 * 图表配色单一真相（Stage 2 治理）：常量与 tokens.css 逐值对齐，禁止第二份色板。
 * screen（大屏暗色）分支运行时读取 CSS 变量 --screen-chart-1..8，
 * 色板定义权留在 CSS token 体系；变量缺失时回落默认色板，不阻塞渲染。
 */

export const CHART_COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#b37feb']

export const COLOR_PRIMARY = '#409eff'
export const COLOR_SUCCESS = '#67c23a'
export const COLOR_WARNING = '#e6a23c'
export const COLOR_DANGER = '#f56c6c'
export const COLOR_INFO = '#909399'
export const COLOR_AXIS = '#c0c4cc'
export const COLOR_AXIS_LABEL = '#909399'
export const COLOR_SPLIT_LINE = '#ebeef5'
/** 与 tokens.css --color-text 对齐（修复历史漂移 #606266） */
export const COLOR_TEXT = '#303133'

export const COLOR_SHAP_POS = '#409eff'
export const COLOR_SHAP_NEG = '#f56c6c'

/** 卡片/图表表面色（对齐 tokens.css --color-surface） */
export const COLOR_SURFACE = '#ffffff'
/** 热力图渐变浅色端（visualMap inRange 起点） */
export const COLOR_HEAT_LOW = '#f2f6fc'

export type ChartTheme = 'default' | 'screen'

let _screenPalette: string[] | null = null

/** 当前主题的序列色板（大屏读 --screen-chart-1..8，缺失回落默认）。 */
export function chartColors(theme: ChartTheme = 'default'): string[] {
  if (theme === 'default') return CHART_COLORS
  if (_screenPalette) return _screenPalette
  if (typeof window === 'undefined' || !document.documentElement) return CHART_COLORS
  const style = getComputedStyle(document.documentElement)
  const cols = Array.from({ length: 8 }, (_, i) =>
    style.getPropertyValue(`--screen-chart-${i + 1}`).trim(),
  ).filter(Boolean)
  _screenPalette = cols.length >= 6 ? cols : CHART_COLORS
  return _screenPalette
}

/** 轴系配色（axisLabel / splitLine / textStyle）。 */
export function axisTheme(theme: ChartTheme = 'default'): {
  axisLabel: string
  splitLine: string
  textStyle: string
} {
  if (theme === 'screen') {
    return { axisLabel: '#8fb3e6', splitLine: 'rgba(120,160,220,0.16)', textStyle: '#dbe9ff' }
  }
  return { axisLabel: COLOR_AXIS_LABEL, splitLine: COLOR_SPLIT_LINE, textStyle: COLOR_TEXT }
}

/** 簇着色（按 cluster id 取色板）。 */
export function clusterColor(idx: number, theme: ChartTheme = 'default'): string {
  const palette = chartColors(theme)
  return palette[idx % palette.length]
}
