<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>

<template>
  <div class="empty">
    <div class="title">{{ title || '暂无数据' }}</div>
    <p class="desc">{{ description || '请先运行对应脚本生成产物后再刷新。' }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty {
  padding: 48px 24px;
  text-align: center;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
}
.title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.desc {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}
</style>
