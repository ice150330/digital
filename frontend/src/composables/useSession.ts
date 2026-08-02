import { computed, ref } from 'vue'
import type { SessionSummary } from '../stores/agent'

export function useSession(sessions: () => SessionSummary[]) {
  const search = ref('')
  const filteredSessions = computed(() => {
    const keyword = search.value.trim().toLowerCase()
    if (!keyword) return sessions()
    return sessions().filter((item) => [
      item.title,
      item.id,
      item.runtime || '',
      String(item.toolCount ?? ''),
      String(item.messageCount ?? ''),
    ].some((value) => value.toLowerCase().includes(keyword)))
  })
  return { search, filteredSessions }
}
