import { getData } from './http'

export interface OverviewData {
  n_rows: number | null
  n_columns: number | null
  positive_rate: number | null
  issues: Array<Record<string, unknown>>
  issue_count: number
  channel_stats: Array<{ channel?: string; n?: number; conversion_rate?: number }>
  email_inconsistent_count: number | null
  invalid_web_metrics_count: number | null
  splits: { n_train?: number; n_valid?: number; n_test?: number } | null
  notes: Record<string, unknown>
}

export interface FeatureMetaData {
  target: string
  feature_columns_raw: string[]
  feature_names_out: string[]
  drop_features: string[]
  never_features: string[]
  categorical_features: string[]
  numeric_features: string[]
  flag_features: string[]
  sample_defaults: Record<string, string | number>
}

// Stage 3：大屏 / L1 描述性聚合
export interface DashboardKpis {
  n_rows: number
  positive_rate: number
  total_ad_spend: number
  avg_ctr: number
  avg_pages_per_visit: number
  repurchase_rate: number
}

export interface FunnelStage {
  stage: string
  label: string
  count: number
  rate_vs_total: number
}

export interface HistBin {
  lo: number
  hi: number
  count: number
}

export interface DashboardData {
  kpis: DashboardKpis
  funnel: FunnelStage[]
  histograms: Record<string, HistBin[]>
  caliber: string
  source: string
  notes: Record<string, unknown>
}

export interface CrossMatrixData {
  row_dim: string
  col_dim: string
  cells: Array<{ row: string; col: string; n: number; conversion_rate: number }>
  row_totals: Array<{ key: string; n: number; conversion_rate: number }>
  col_totals: Array<{ key: string; n: number; conversion_rate: number }>
  caliber: string
}

export function fetchOverview() {
  return getData<OverviewData>('/data/overview')
}

export function fetchFeatureMeta() {
  return getData<FeatureMetaData>('/meta/features')
}

export function fetchDashboard() {
  return getData<DashboardData>('/data/dashboard')
}

export function fetchCrossMatrix(rowDim = 'campaign_channel', colDim = 'campaign_type') {
  return getData<CrossMatrixData>(
    `/data/cross-matrix?row_dim=${encodeURIComponent(rowDim)}&col_dim=${encodeURIComponent(colDim)}`,
  )
}
