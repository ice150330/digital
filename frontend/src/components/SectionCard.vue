<script setup lang="ts">
import { ElCard } from 'element-plus'
import LoadingState from './LoadingState.vue'

withDefaults(defineProps<{
  title?: string
  subtitle?: string
  loading?: boolean
}>(), {
  loading: false,
})
</script>

<template>
  <ElCard shadow="never" class="section-card">
    <template v-if="title || $slots.actions" #header>
      <div class="section-card-header">
        <div class="section-card-titles">
          <span v-if="title" class="section-card-title">{{ title }}</span>
          <span v-if="subtitle" class="section-card-subtitle">{{ subtitle }}</span>
        </div>
        <div v-if="$slots.actions" class="section-card-actions">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <LoadingState v-if="loading" />
    <slot v-else />
  </ElCard>
</template>

<style scoped>
.section-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-width: 0;
}
.section-card-titles {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}
.section-card-title {
  color: var(--text-title);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  white-space: nowrap;
}
.section-card-subtitle {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.section-card-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}
</style>
