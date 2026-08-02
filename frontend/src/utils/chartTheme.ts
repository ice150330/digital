/**
 * 图表配色单一真相：与 Halo v2 tokens.css 逐值对齐。
 * /screen 已回到浅色工作台框架，不再维护独立暗色 screen 分支。
 */

export const CHART_COLORS = ['#5749f4', '#14b8a6', '#f59e0b', '#8b5cf6', '#ec4899', '#22c55e', '#f97316', '#06b6d4']

export const COLOR_PRIMARY = '#5749f4'
export const COLOR_SUCCESS = '#22c55e'
export const COLOR_WARNING = '#f59e0b'
export const COLOR_DANGER = '#ef4444'
export const COLOR_INFO = '#0ea5e9'
export const COLOR_AXIS = '#e1e2e5'
export const COLOR_AXIS_LABEL = '#616167'
export const COLOR_SPLIT_LINE = '#e1e2e5'
export const COLOR_TEXT = '#403f51'

export const COLOR_SHAP_POS = '#5749f4'
export const COLOR_SHAP_NEG = '#ef4444'

/** 卡片/图表表面色（对齐 tokens.css --color-surface） */
export const COLOR_SURFACE = '#ffffff'
/** 热力图渐变浅色端（visualMap inRange 起点） */
export const COLOR_HEAT_LOW = '#f5f5f5'
export const COLOR_HEAT_LABEL = '#2a2933'
export const COLOR_HEAT_BORDER = 'rgba(255,255,255,0.88)'

export type ChartTheme = 'default'

/** 当前主题的序列色板。 */
export function chartColors(theme: ChartTheme = 'default'): string[] {
  return theme === 'default' ? CHART_COLORS : CHART_COLORS
}

/** 轴系配色（axisLabel / splitLine / textStyle）。 */
export function axisTheme(theme: ChartTheme = 'default'): {
  axisLabel: string
  splitLine: string
  textStyle: string
} {
  return theme === 'default'
    ? { axisLabel: COLOR_AXIS_LABEL, splitLine: COLOR_SPLIT_LINE, textStyle: COLOR_TEXT }
    : { axisLabel: COLOR_AXIS_LABEL, splitLine: COLOR_SPLIT_LINE, textStyle: COLOR_TEXT }
}

/** 簇着色（按 cluster id 取色板）。 */
export function clusterColor(idx: number, theme: ChartTheme = 'default'): string {
  const palette = chartColors(theme)
  return palette[idx % palette.length]
}
