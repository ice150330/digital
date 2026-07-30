import { postData } from './http'

export interface BudgetCurvePoint {
  k: number
  expected_conversions: number
  expected_net: number
  expected_revenue: number
  budget_used: number
  avg_proba: number
}

export interface ReachRow {
  rank: number
  customerid?: number
  proba: number
  expected_value: number
}

export interface BudgetSimulateData {
  run_id: string
  params: {
    value_per_conversion: number
    cost_per_contact: number
    budget?: number | null
  }
  n_population: number
  curve: BudgetCurvePoint[]
  recommended_k: number
  recommended?: BudgetCurvePoint | null
  calibrated: boolean
  top_list: ReachRow[]
  export_path?: string | null
  disclaimer: string
}

export function simulateBudget(body: {
  budget?: number | null
  value_per_conversion?: number
  cost_per_contact?: number
  run_id?: string
  export?: boolean
  n_points?: number
}) {
  return postData<BudgetSimulateData>('/simulate/budget', body)
}
