import { onBeforeUnmount, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAppStore } from '../stores/app'

export function useHealth(intervalMs = 30000) {
  const store = useAppStore()
  const { health, healthError, healthLoading } = storeToRefs(store)
  let timer: number | null = null

  async function refreshHealth() {
    await store.loadHealth()
  }

  onMounted(() => {
    void refreshHealth()
    timer = window.setInterval(() => { void refreshHealth() }, intervalMs)
  })

  onBeforeUnmount(() => {
    if (timer != null) window.clearInterval(timer)
  })

  return { health, healthError, healthLoading, refreshHealth }
}
