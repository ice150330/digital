<script setup lang="ts">
import Icon from './Icon.vue'

withDefaults(defineProps<{ content?: string }>(), {
  content: '以下洞察基于历史数据中的相关关系与模型估计，不构成因果证明，也不构成实际投放收益承诺。',
})
</script>

<template>
  <div class="disclaimer-banner" role="note">
    <Icon icon="uil:info-circle" size="sm" title="口径说明" />
    <span>{{ content }}</span>
  </div>
</template>

<style scoped>
.disclaimer-banner { display: flex; align-items: flex-start; gap: var(--space-2); padding: var(--space-3) var(--space-4); border: 1px solid var(--color-warning-border); border-left: var(--space-1) solid var(--color-warning); border-radius: var(--radius-md); background: var(--color-warning-bg); color: var(--text-body); font-size: var(--font-size-xs); line-height: 1.6; }
.disclaimer-banner span { min-width: 0; overflow-wrap: anywhere; }
.disclaimer-banner :deep(.app-icon) { flex: 0 0 auto; margin-top: var(--space-1); color: var(--color-warning); }
</style>
