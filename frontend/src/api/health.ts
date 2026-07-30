import { getData } from './http'

export interface HealthData {
  status: string
  app: string
  version: string
  database_ok: boolean
  campaigns_count: number | null
  message: string | null
}

export async function fetchHealth() {
  return getData<HealthData>('/health')
}
