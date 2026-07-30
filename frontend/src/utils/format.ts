/** 数字与百分比格式化（展示用） */

export function formatPercent(v: number | null | undefined, digits = 2): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return `${(Number(v) * 100).toFixed(digits)}%`
}

export function formatProba(v: number | null | undefined, digits = 4): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Number(v).toFixed(digits)
}

export function formatMetric(v: number | null | undefined, digits = 4): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Number(v).toFixed(digits)
}

export function formatInt(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Math.round(Number(v)).toLocaleString('zh-CN')
}
