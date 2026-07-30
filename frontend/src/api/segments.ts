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

// ---------------------------------------------------------------------------
// 阶段9：分群对比 / 投影
// ---------------------------------------------------------------------------

export interface SegmentCompareRow {
  algo: string
  k: number
  silhouette?: number
  calinski_harabasz?: number
  bic?: number
  error?: string
}

export interface SegmentCompareData {
  kmeans_k: number
  comparison: SegmentCompareRow[]
  stability: {
    algo: string
    k: number
    n_boot: number
    ari_mean: number
    ari_std: number
    note?: string
  }
  auto_names?: Record<string, string>
  disclaimer?: string
}

export interface SegmentProjectionData {
  method: string
  explained_variance: number[]
  n_points: number
  points: Array<{ x: number; y: number; cluster: number; customer_id?: number }>
  disclaimer?: string
}

export function fetchSegmentCompare() {
  return getData<SegmentCompareData>('/segments/compare')
}

export function fetchSegmentProjection() {
  return getData<SegmentProjectionData>('/segments/projection')
}
