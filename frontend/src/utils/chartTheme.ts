/**
 * 图表配色：统一从 tokens.css 派生（避免各组件硬编码 hex）。
 * 与 frontend/src/styles/tokens.css 的 --color-chart-* / --color-* 对齐。
 */

export const CHART_COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9b59b6']

export const COLOR_PRIMARY = '#409eff'
export const COLOR_SUCCESS = '#67c23a'
export const COLOR_WARNING = '#e6a23c'
export const COLOR_DANGER = '#f56c6c'
export const COLOR_INFO = '#909399'
export const COLOR_AXIS = '#c0c4cc'
export const COLOR_AXIS_LABEL = '#909399'
export const COLOR_SPLIT_LINE = '#ebeef5'
export const COLOR_TEXT = '#606266'

export const COLOR_SHAP_POS = '#409eff'
export const COLOR_SHAP_NEG = '#f56c6c'

/** 簇着色（按 cluster id 取色板） */
export function clusterColor(idx: number): string {
  return CHART_COLORS[idx % CHART_COLORS.length]
}
