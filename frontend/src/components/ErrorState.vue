<script setup lang="ts">
import Button from './Button.vue'
import Icon from './Icon.vue'

defineProps<{
  title?: string
  message: string
}>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="err" role="alert">
    <span class="err-icon"><Icon icon="uil:exclamation-octagon" size="lg" /></span>
    <div class="err-copy"><strong>{{ title || '加载失败' }}</strong><p>{{ message }}</p></div>
    <Button variant="outline" size="sm" icon="uil:redo" @click="emit('retry')">重试</Button>
  </div>
</template>

<style scoped>
.err {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-danger-border);
  border-radius: var(--radius-card);
  background: var(--color-danger-bg);
}
.err-icon { display: grid; width: var(--space-10); height: var(--space-10); flex: 0 0 auto; place-items: center; border-radius: var(--radius-full); background: var(--color-white); color: var(--color-danger); }
.err-copy { min-width: 0; flex: 1; }
.err-copy strong { color: var(--color-danger-text); font-size: var(--font-size-sm); }
.err-copy p { margin: var(--space-1) 0 0; color: var(--text-body); font-size: var(--font-size-xs); line-height: 1.6; }
</style>
