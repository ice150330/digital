import { ref } from 'vue'

export function useStreamChat() {
  const stopped = ref(false)
  let aborter: (() => void) | null = null

  function attach(abort: () => void) {
    stopped.value = false
    aborter = abort
  }

  function stop() {
    stopped.value = true
    aborter?.()
    aborter = null
  }

  function release() {
    aborter = null
  }

  return { stopped, attach, stop, release }
}
