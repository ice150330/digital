import { getData, postData } from './http'

export interface ClusterRow {
  cluster_id: number
  n?: number
  share?: number
  conversion_rate?: number
  conversion_note?: string
  profile_means?: Record<string, number | null>
}

export interface SegmentsData {
  method?: string
  n_clusters?: number
  n_samples?: number
  disclaimer?: string
  clusters: ClusterRow[]
  feature_columns?: string[]
  label_excluded?: boolean
}

export function fetchSegments() {
  return getData<SegmentsData>('/segments')
}

export function assignSegment(body: { customer_id?: number; features?: Record<string, unknown> }) {
  return postData<{
    cluster_id: number
    distance?: number
    customer_id?: number
    cluster?: ClusterRow
    disclaimer?: string
  }>('/segments/assign', body)
}
