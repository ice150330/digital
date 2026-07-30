<script setup lang="ts">
import { ElAlert, ElButton } from 'element-plus'

defineProps<{
  title?: string
  message: string
}>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="err">
    <ElAlert type="error" show-icon :closable="false" :title="title || '加载失败'" :description="message" />
    <ElButton class="retry" @click="emit('retry')">重试</ElButton>
  </div>
</template>

<style scoped>
.err {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}
.retry {
  margin-left: 0;
}
</style>
