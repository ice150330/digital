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

// ---------------------------------------------------------------------------
// 阶段9：增强评估端点
// ---------------------------------------------------------------------------

export interface CurvesData {
  run_id: string
  pr_auc?: number
  roc_auc?: number
  ci: { pr_auc_low?: number; pr_auc_high?: number; n_boot?: number; level?: number }
  cv: { pr_auc_mean?: number; pr_auc_std?: number; folds?: number }
  pr_curve: { precision: number[]; recall: number[]; n_points?: number }
  roc_curve: { fpr: number[]; tpr: number[]; n_points?: number }
}

export interface CalibrationSide {
  brier: number
  log_loss: number
  ece: number
  bins: Array<{ bin: number; count: number; mean_pred: number; frac_pos: number }>
}

export interface CalibrationData {
  run_id: string
  method: string
  valid_brier_compare?: Record<string, number>
  before: CalibrationSide
  after: CalibrationSide
  note?: string
}

export interface LiftDecile {
  decile: number
  n: number
  positives: number
  cum_n: number
  capture_rate: number
  lift: number
}

export interface LiftData {
  run_id: string
  lift_deciles: LiftDecile[]
  note?: string
}

export interface ThresholdScanRow {
  threshold: number
  precision: number
  recall: number
  f1: number
  expected_cost: number
}

export interface ThresholdScanData {
  run_id: string
  cost_fp: number
  cost_fn: number
  cost_note?: string
  rows: ThresholdScanRow[]
  best_by_cost?: ThresholdScanRow
  current_threshold?: number
}

export function fetchCurves(runId?: string) {
  return getData<CurvesData>('/models/curves', runId ? { run_id: runId } : undefined)
}

export function fetchCalibration(runId?: string) {
  return getData<CalibrationData>('/models/calibration', runId ? { run_id: runId } : undefined)
}

export function fetchLift(runId?: string) {
  return getData<LiftData>('/models/lift', runId ? { run_id: runId } : undefined)
}

export function fetchThresholdScan(runId?: string) {
  return getData<ThresholdScanData>(
    '/models/threshold-scan',
    runId ? { run_id: runId } : undefined,
  )
}
