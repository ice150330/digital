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

// ---------------------------------------------------------------------------
// 阶段9：PDP / 反事实
// ---------------------------------------------------------------------------

export interface PdpBundle {
  run_id: string
  features: Record<
    string,
    {
      feature: string
      grid: number[]
      pdp: number[]
      ice: Array<{ index: number; values: number[] }>
      disclaimer?: string
    }
  >
  disclaimer?: string
}

export interface PdpSingle {
  run_id: string
  feature: string
  grid: number[]
  pdp: number[]
  ice: Array<{ index: number; values: number[] }>
  disclaimer?: string
}

export interface CounterfactualData {
  run_id: string
  customer_id?: number | null
  curve?: {
    feature: string
    base_value: number
    base_proba: number
    grid: number[]
    proba: number[]
    disclaimer: string
  }
  counterfactual?: {
    base_proba: number
    target_proba: number
    final_proba: number
    achieved: boolean
    n_steps: number
    steps: Array<{ feature: string; from: number; to: number; proba_after: number }>
    disclaimer: string
  }
}

export function fetchPdp(feature?: string, runId?: string) {
  const params: Record<string, string> = {}
  if (feature) params.feature = feature
  if (runId) params.run_id = runId
  return getData<PdpBundle | PdpSingle>('/explain/pdp', Object.keys(params).length ? params : undefined)
}

export function explainCounterfactual(body: {
  customer_id?: number
  features?: Record<string, unknown>
  feature?: string
  target_proba?: number
  run_id?: string
  grid_size?: number
  max_steps?: number
}) {
  return postData<CounterfactualData>('/explain/counterfactual', body)
}
