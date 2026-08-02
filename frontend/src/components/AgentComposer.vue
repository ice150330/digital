<script setup lang="ts">
import { computed } from 'vue'
import Button from './Button.vue'

const props = withDefaults(defineProps<{
  modelValue: string
  loading?: boolean
  streaming?: boolean
  placeholder?: string
  chips?: string[]
}>(), { placeholder: '输入一个数据问题…', chips: () => [] })
const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: [value?: string]
  stop: []
}>()
const canSend = computed(() => Boolean(props.modelValue.trim()) && !props.loading && !props.streaming)
function onKeydown(event: KeyboardEvent) {
  if (event.ctrlKey && event.key === 'Enter') {
    event.preventDefault()
    if (canSend.value) emit('send')
  }
}
</script>

<template>
  <div class="composer">
    <div v-if="chips.length" class="composer-chips">
      <button v-for="chip in chips" :key="chip" type="button" :disabled="loading || streaming" @click="emit('send', chip)">{{ chip }}</button>
    </div>
    <div class="composer-row">
      <textarea :value="modelValue" :placeholder="placeholder" :disabled="loading && !streaming" rows="3" @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)" @keydown="onKeydown" />
      <Button v-if="streaming" variant="outline" icon="uil:stop-circle" @click="emit('stop')">停止</Button>
      <Button v-else variant="primary" icon="uil:message" :loading="loading" :disabled="!canSend" @click="emit('send')">发送</Button>
    </div>
    <span class="composer-hint">Ctrl + Enter 发送 · 数字来自后端工具结果</span>
  </div>
</template>

<style scoped>
.composer { display: flex; flex-direction: column; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--bg-card); box-shadow: var(--shadow-sm); }
.composer-chips { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.composer-chips button { min-height: 28px; padding: 0 var(--space-3); border: 1px solid var(--color-primary-100); border-radius: var(--radius-full); background: var(--color-primary-50); color: var(--color-primary-700); cursor: pointer; font-size: var(--font-size-xs); }
.composer-chips button:hover:not(:disabled) { border-color: var(--color-primary-300); background: var(--color-primary-100); }
.composer-chips button:disabled { cursor: not-allowed; opacity: 0.55; }
.composer-row { display: flex; align-items: flex-end; gap: var(--space-3); }
.composer-row textarea { min-height: 80px; flex: 1; resize: vertical; padding: var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-md); outline: 0; background: var(--bg-card); color: var(--text-body); font-size: var(--font-size-md); line-height: 1.5; }
.composer-row textarea:focus { border-color: var(--border-focus); box-shadow: 0 0 0 3px var(--color-primary-50); }
.composer-hint { color: var(--text-secondary); font-size: var(--font-size-xs); }
@media (max-width: 640px) {
  .composer-row { align-items: stretch; flex-direction: column; }
  .composer-row textarea { width: 100%; }
}
</style>
