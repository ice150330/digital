<script setup lang="ts">
import Icon from './Icon.vue'

withDefaults(defineProps<{
  variant?: 'primary' | 'default' | 'outline' | 'soft' | 'danger' | 'text' | 'icon-only'
  size?: 'sm' | 'md' | 'lg'
  icon?: string
  loading?: boolean
  disabled?: boolean
  nativeType?: 'button' | 'submit' | 'reset'
}>(), {
  variant: 'default',
  size: 'md',
  nativeType: 'button',
})
</script>

<template>
  <button
    class="app-button"
    :class="[`is-${variant}`, `is-${size}`, { 'is-loading': loading }]"
    :type="nativeType"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
  >
    <span v-if="loading" class="button-spinner" aria-hidden="true" />
    <Icon v-else-if="icon" :icon="icon" size="sm" />
    <span v-if="$slots.default"><slot /></span>
  </button>
</template>

<style scoped>
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  transition: background var(--motion-duration-fast) var(--motion-easing-default), border-color var(--motion-duration-fast) var(--motion-easing-default), color var(--motion-duration-fast) var(--motion-easing-default);
}
.app-button:focus-visible {
  outline: 1px solid var(--color-primary-500);
  outline-offset: 1px;
}
.app-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.is-sm { min-height: var(--control-height-sm); padding: 0 var(--space-2); font-size: var(--font-size-xs); }
.is-md { min-height: var(--control-height-md); padding: 0 var(--space-3); }
.is-lg { min-height: var(--control-height-lg); padding: 0 var(--space-4); font-size: var(--font-size-md); }
.is-primary { background: var(--color-primary-500); color: var(--color-white); }
.is-primary:hover:not(:disabled) { background: var(--color-primary-600); }
.is-default { background: var(--bg-card); border-color: var(--border-default); color: var(--text-body); }
.is-default:hover:not(:disabled), .is-outline:hover:not(:disabled) { border-color: var(--border-hover); color: var(--color-primary-700); background: var(--color-primary-50); }
.is-outline { background: transparent; border-color: var(--border-default); color: var(--text-body); }
.is-soft { background: var(--color-primary-50); color: var(--color-primary-700); }
.is-soft:hover:not(:disabled) { background: var(--color-primary-100); }
.is-danger { background: var(--color-danger); color: var(--color-white); }
.is-danger:hover:not(:disabled) { background: var(--color-danger-hover); }
.is-text { background: transparent; color: var(--color-primary-600); padding-inline: var(--space-2); }
.is-text:hover:not(:disabled) { background: var(--color-primary-50); }
.is-icon-only { width: var(--control-height-md); min-width: var(--control-height-md); padding-inline: 0; background: transparent; border-color: var(--border-default); color: var(--text-body); }
.is-icon-only:hover:not(:disabled) { border-color: var(--border-hover); color: var(--color-primary-700); background: var(--color-primary-50); }
.is-sm.is-icon-only { width: var(--control-height-sm); min-width: var(--control-height-sm); }
.is-lg.is-icon-only { width: var(--control-height-lg); min-width: var(--control-height-lg); }
.button-spinner { width: var(--space-3); height: var(--space-3); border: 2px solid currentColor; border-right-color: transparent; border-radius: var(--radius-full); animation: spin var(--motion-duration-slow) linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .button-spinner { animation: none; } }
</style>
