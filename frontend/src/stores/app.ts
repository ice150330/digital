import { defineStore } from 'pinia'
import { fetchHealth, type HealthData } from '../api/health'
import { setRuntime } from '../api/agent'

export const useAppStore = defineStore('app', {
  state: () => ({
    health: null as HealthData | null,
    healthError: null as string | null,
    healthLoading: false,
    sidebarCollapsed: false,
    runtime: 'pi',
  }),
  getters: {
    defaultRunId: (state) => state.health?.default_run_id || null,
  },
  actions: {
    async loadHealth() {
      this.healthLoading = true
      this.healthError = null
      try {
        const { data } = await fetchHealth()
        this.health = data
      } catch (error) {
        this.health = null
        this.healthError = error instanceof Error ? error.message : '健康状态加载失败'
      } finally {
        this.healthLoading = false
      }
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    async changeRuntime(runtime: string) {
      await setRuntime(runtime)
      this.runtime = runtime
    },
  },
})
