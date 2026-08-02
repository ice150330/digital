<script setup lang="ts">
import Icon from './Icon.vue'
import Button from './Button.vue'
import { useSession } from '../composables/useSession'
import type { SessionSummary } from '../stores/agent'

const props = defineProps<{
  sessions: SessionSummary[]
  activeId: string | null
  loading?: boolean
}>()
const emit = defineEmits<{
  select: [id: string]
  create: []
  delete: [id: string]
}>()
const { search, filteredSessions: filtered } = useSession(() => props.sessions)
</script>

<template>
  <aside class="session-list">
    <div class="session-head">
      <div>
        <strong>分析会话</strong>
        <span>{{ sessions.length }} 条记录</span>
      </div>
      <Button variant="soft" size="sm" icon="uil:plus" aria-label="新建会话" @click="emit('create')">新建</Button>
    </div>
    <label class="session-search">
      <Icon icon="uil:search" size="sm" />
      <input v-model="search" type="search" placeholder="搜索会话" aria-label="搜索会话" />
    </label>
    <div v-if="loading" class="session-empty">正在加载会话…</div>
    <div v-else-if="!filtered.length" class="session-empty">暂无历史会话</div>
    <div v-else class="session-items">
      <button
        v-for="item in filtered"
        :key="item.id"
        type="button"
        class="session-item"
        :class="{ active: item.id === activeId }"
        @click="emit('select', item.id)"
      >
        <span class="session-item-main">
          <strong>{{ item.title }}</strong>
          <small>{{ new Date(item.updatedAt).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }}</small>
        </span>
        <span class="session-actions" @click.stop>
          <Button
            variant="icon-only"
            size="sm"
            icon="uil:trash-alt"
            aria-label="删除会话"
            @click="emit('delete', item.id)"
          />
        </span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.session-list { display: flex; min-height: 520px; flex-direction: column; gap: var(--space-4); padding: var(--space-4); background: var(--bg-card); border: 1px solid var(--border-default); border-radius: var(--radius-card); }
.session-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.session-head strong { display: block; color: var(--text-title); font-size: var(--font-size-md); }
.session-head span { display: block; margin-top: var(--space-1); color: var(--text-secondary); font-size: var(--font-size-xs); }
.session-search { display: flex; align-items: center; gap: var(--space-2); min-height: var(--control-height-md); padding: 0 var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-md); color: var(--text-secondary); }
.session-search:focus-within { border-color: var(--border-focus); box-shadow: 0 0 0 3px var(--color-primary-50); }
.session-search input { width: 100%; border: 0; outline: 0; background: transparent; color: var(--text-body); font-size: var(--font-size-sm); }
.session-items { display: flex; flex-direction: column; gap: var(--space-1); overflow: auto; }
.session-item { display: flex; align-items: center; gap: var(--space-2); width: 100%; padding: var(--space-3); border: 1px solid transparent; border-radius: var(--radius-md); background: transparent; color: var(--text-body); cursor: pointer; text-align: left; transition: background var(--motion-duration-fast) var(--motion-easing-default), border-color var(--motion-duration-fast) var(--motion-easing-default); }
.session-item:hover { background: var(--bg-subtle); }
.session-item.active { border-color: var(--color-primary-100); background: var(--color-primary-50); }
.session-item-main { min-width: 0; flex: 1; }
.session-item-main strong { display: block; overflow: hidden; color: var(--text-title); font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); text-overflow: ellipsis; white-space: nowrap; }
.session-item-main small { display: block; margin-top: var(--space-1); color: var(--text-secondary); font-size: var(--font-size-xs); }
.session-actions { color: var(--text-placeholder); }
.session-actions:hover { color: var(--color-danger); }
.session-empty { padding: var(--space-8) var(--space-4); color: var(--text-secondary); font-size: var(--font-size-sm); text-align: center; }
@media (max-width: 640px) {
  .session-list { min-height: 360px; }
  .session-items { max-height: 240px; }
}
</style>
