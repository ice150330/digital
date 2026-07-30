import { getData } from './http'

export interface RuleRow {
  antecedents: string
  consequents: string
  support: number
  confidence: number
  lift: number
}

export interface RulesData {
  method?: string
  n_rules?: number
  min_lift?: number
  disclaimer: string
  rules: RuleRow[]
}

export function fetchRules(minLift = 1.0, limit = 50) {
  return getData<RulesData>('/rules', { min_lift: minLift, limit })
}
