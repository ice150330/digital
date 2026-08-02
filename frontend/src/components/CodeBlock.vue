<script setup lang="ts">
import { ref } from 'vue'
import Button from './Button.vue'

const props = defineProps<{ code: string; label?: string }>()
const copied = ref(false)

async function copyCode() {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    window.setTimeout(() => { copied.value = false }, 1600)
  } catch {
    copied.value = false
  }
}
</script>

<template>
  <div class="code-shell">
    <div class="code-toolbar">
      <span>{{ label || '命令' }}</span>
      <Button
        variant="icon-only"
        size="sm"
        :icon="copied ? 'uil:check' : 'uil:copy'"
        :aria-label="copied ? '已复制' : '复制命令'"
        :title="copied ? '已复制' : '复制命令'"
        @click="copyCode"
      />
    </div>
    <pre><code>{{ code }}</code></pre>
  </div>
</template>

<style scoped>
.code-shell { overflow: hidden; border: 1px solid var(--color-gray-700); border-radius: var(--radius-lg); background: var(--color-code-dark-bg); }
.code-toolbar { display: flex; align-items: center; justify-content: space-between; min-height: var(--space-10); padding: 0 var(--space-3); border-bottom: 1px solid var(--color-gray-700); color: var(--color-gray-400); font-size: var(--font-size-xs); }
.code-toolbar :deep(.app-button) { border-color: var(--color-gray-700); color: var(--color-code-dark-text); }
pre { margin: 0; padding: var(--space-4); overflow: auto; color: var(--color-code-dark-text); font-family: var(--font-family-code); font-size: var(--font-size-xs); line-height: 1.7; }
pre code { padding: 0; border-radius: 0; background: transparent; color: inherit; font: inherit; }
</style>
