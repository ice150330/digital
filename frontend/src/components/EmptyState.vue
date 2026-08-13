<script setup lang="ts">
import Button from './Button.vue'
import Icon from './Icon.vue'

defineProps<{
  icon?: string
  title?: string
  description?: string
  actionText?: string
}>()
const emit = defineEmits<{ action: [] }>()
</script>

<template>
  <div class="empty">
    <span class="empty-icon"><Icon :icon="icon || 'uil:folder-open'" size="lg" /></span>
    <div class="title">{{ title || '暂无数据' }}</div>
    <p class="desc">{{ description || '请先运行对应脚本生成产物后再刷新。' }}</p>
    <Button v-if="actionText" class="action" variant="soft" size="sm" @click="emit('action')">{{ actionText }}</Button>
    <slot />
  </div>
</template>

<style scoped>
.empty {
  padding: var(--space-5) var(--space-4);
  text-align: center;
  background: var(--bg-card);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-card);
  color: var(--text-body);
}
.empty-icon { display: grid; width: 36px; height: 36px; margin: 0 auto var(--space-2); place-items: center; border-radius: var(--radius-sm); background: var(--bg-subtle); color: var(--text-secondary); }
.title {
  margin-bottom: var(--space-1);
  color: var(--text-title);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
}
.desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}
.action { margin-top: var(--space-4); }
</style>
