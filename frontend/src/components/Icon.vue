<script setup lang="ts">
import { computed } from 'vue'
import { Icon as IconifyIcon } from '@iconify/vue'

const props = withDefaults(defineProps<{
  icon: string
  size?: 'sm' | 'md' | 'lg' | number
  color?: string
  title?: string
}>(), {
  size: 'md',
})

const sizeValue = computed(() => {
  if (typeof props.size === 'number') return `${props.size}px`
  return {
    sm: 'var(--icon-size-sm)',
    md: 'var(--icon-size-md)',
    lg: 'var(--icon-size-lg)',
  }[props.size]
})
</script>

<template>
  <IconifyIcon
    :icon="icon"
    :style="{ color, width: sizeValue, height: sizeValue }"
    :title="title"
    :aria-hidden="title ? undefined : true"
    class="app-icon"
  />
</template>

<style scoped>
.app-icon {
  display: inline-block;
  flex: 0 0 auto;
  max-width: none;
  vertical-align: middle;
}
</style>
