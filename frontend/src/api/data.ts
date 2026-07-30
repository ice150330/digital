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

export function fetchOverview() {
  return getData<OverviewData>('/data/overview')
}

export function fetchFeatureMeta() {
  return getData<FeatureMetaData>('/meta/features')
}
