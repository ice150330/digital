import { getData, postData } from './http'

export interface MetricRow {
  run_id: string
  exp_id?: string
  model_name?: string
  pr_auc?: number
  roc_auc?: number
  f1?: number
  accuracy?: number
  threshold?: number
  [key: string]: unknown
}

export interface MetricsListData {
  items: MetricRow[]
  primary_metric: string
  accuracy_note: string
}

export interface PredictData {
  proba: number
  label: number
  threshold: number
  run_id: string
  model_name: string
  customer_id?: number | null
}

export function fetchMetrics() {
  return getData<MetricsListData>('/models/metrics')
}

export function fetchMetric(runId: string) {
  return getData<MetricRow>(`/models/metrics/${runId}`)
}

export function predict(body: {
  customer_id?: number
  features?: Record<string, unknown>
  run_id?: string
}) {
  return postData<PredictData>('/models/predict', body)
}

export interface BatchPredictData {
  run_id: string
  model_name: string
  threshold: number
  n_requested: number
  n_ok: number
  n_error: number
  items: PredictData[]
  errors: Array<{ customer_id?: number; code?: string; message?: string }>
  max_items: number
  note?: string
}

export function predictBatch(body: {
  customer_ids?: number[]
  rows?: Record<string, unknown>[]
  run_id?: string
}) {
  return postData<BatchPredictData>('/models/predict/batch', body)
}
