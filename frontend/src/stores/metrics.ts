import { defineStore } from 'pinia'
import { fetchMetric, fetchMetrics, type MetricRow } from '../api/models'

export const useMetricsStore = defineStore('metrics', {
  state: () => ({
    leaderboard: null as MetricRow[] | null,
    defaultMetrics: null as MetricRow | null,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async loadLeaderboard() {
      this.loading = true
      this.error = null
      try {
        const { data } = await fetchMetrics()
        this.leaderboard = data.items
        return data.items
      } catch (error) {
        this.error = error instanceof Error ? error.message : '模型指标加载失败'
        return []
      } finally {
        this.loading = false
      }
    },
    async loadRunMetrics(runId: string) {
      const { data } = await fetchMetric(runId)
      this.defaultMetrics = data
      return data
    },
  },
})
