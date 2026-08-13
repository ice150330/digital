/**
 * 图表配色单一真相：与 Data Dense v3 tokens.css 逐值对齐。
 * /screen 已回到浅色工作台框架，不再维护独立暗色 screen 分支。
 * 索引语义锁死：CHART_COLORS[2]=未转化、[5]=转化（ScreenSankeyOrbit 按索引引用），前 6 位禁止重排。
 */

export const CHART_COLORS = ['#3b82f6', '#14b8a6', '#f59e0b', '#64748b', '#0ea5e9', '#22c55e', '#f97316', '#94a3b8']

export const COLOR_PRIMARY = '#3b82f6'
export const COLOR_SUCCESS = '#22c55e'
export const COLOR_WARNING = '#f59e0b'
export const COLOR_DANGER = '#ef4444'
export const COLOR_INFO = '#0ea5e9'
export const COLOR_AXIS = '#e2e8f0'
export const COLOR_AXIS_LABEL = '#64748b'
export const COLOR_SPLIT_LINE = '#e2e8f0'
export const COLOR_TEXT = '#1e293b'

export const COLOR_SHAP_POS = '#3b82f6'
export const COLOR_SHAP_NEG = '#ef4444'

/** 卡片/图表表面色（对齐 tokens.css --color-surface） */
export const COLOR_SURFACE = '#ffffff'
/** 热力图渐变浅色端（visualMap inRange 起点） */
export const COLOR_HEAT_LOW = '#f1f5f9'
export const COLOR_HEAT_LABEL = '#0f172a'
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
