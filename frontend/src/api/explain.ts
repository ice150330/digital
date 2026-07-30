import { getData, postData } from './http'

export interface ShapFeature {
  name: string
  feature_value?: unknown
  shap_value?: number
  mean_abs_shap?: number
}

export interface GlobalExplainData {
  run_id: string
  method: string
  n_samples?: number
  top_features: ShapFeature[]
}

export interface CustomerExplainData {
  run_id: string
  model_name?: string
  method: string
  proba?: number
  label?: number
  threshold?: number
  customer_id?: number | null
  top_features: ShapFeature[]
}

export function fetchGlobalExplain(runId?: string) {
  return getData<GlobalExplainData>('/explain/global', runId ? { run_id: runId } : undefined)
}

export function explainCustomer(body: {
  customer_id?: number
  features?: Record<string, unknown>
  run_id?: string
  top_k?: number
}) {
  return postData<CustomerExplainData>('/explain/customer', body)
}
