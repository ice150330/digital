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

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function shortId(id: string) {
  return id.slice(0, 8)
}
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
          <span class="session-title-row">
            <strong>{{ item.title }}</strong>
            <span class="runtime-pill">{{ item.runtime || 'unknown' }}</span>
          </span>
          <small class="session-time"><Icon icon="uil:clock" size="sm" />{{ formatDate(item.updatedAt) }}</small>
          <span class="session-meta-line">
            <span><Icon icon="uil:comment-alt-lines" size="sm" />{{ item.messageCount ?? 0 }} 消息</span>
            <span><Icon icon="uil:wrench" size="sm" />{{ item.toolCount ?? 0 }} 工具</span>
            <span class="session-short-id">#{{ shortId(item.id) }}</span>
          </span>
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
.session-list { display: flex; min-height: 480px; height: min(720px, calc(100vh - 180px)); min-width: 0; flex-direction: column; gap: var(--space-4); overflow: hidden; padding: var(--space-4); background: var(--bg-card); border: 1px solid var(--border-default); border-radius: var(--radius-card); }
.session-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.session-head strong { display: block; color: var(--text-title); font-size: var(--font-size-md); }
.session-head span { display: block; margin-top: var(--space-1); color: var(--text-secondary); font-size: var(--font-size-xs); }
.session-search { display: flex; align-items: center; gap: var(--space-2); min-height: var(--control-height-md); padding: 0 var(--space-3); border: 1px solid var(--border-default); border-radius: var(--radius-md); color: var(--text-secondary); }
.session-search:focus-within { border-color: var(--border-focus); box-shadow: 0 0 0 3px var(--color-primary-50); }
.session-search input { width: 100%; border: 0; outline: 0; background: transparent; color: var(--text-body); font-size: var(--font-size-sm); }
.session-items { display: flex; min-height: 0; flex: 1; flex-direction: column; gap: var(--space-2); overflow-y: auto; padding-right: var(--space-1); }
.session-item { display: flex; align-items: flex-start; gap: var(--space-2); width: 100%; padding: var(--space-3); border: 1px solid transparent; border-radius: var(--radius-md); background: transparent; color: var(--text-body); cursor: pointer; text-align: left; transition: background var(--motion-duration-fast) var(--motion-easing-default), border-color var(--motion-duration-fast) var(--motion-easing-default); }
.session-item:hover { background: var(--bg-subtle); }
.session-item.active { border-color: var(--color-primary-100); background: var(--color-primary-50); }
.session-item-main { min-width: 0; flex: 1; }
.session-title-row { display: flex; min-width: 0; align-items: center; gap: var(--space-2); }
.session-item-main strong { display: block; min-width: 0; flex: 1; overflow: hidden; color: var(--text-title); font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); text-overflow: ellipsis; white-space: nowrap; }
.runtime-pill { display: inline-flex; max-width: 76px; min-height: var(--tag-height-sm); flex: 0 0 auto; align-items: center; padding: 0 var(--space-2); overflow: hidden; border-radius: var(--radius-full); background: var(--bg-subtle); color: var(--text-secondary); font-size: var(--font-size-xs); line-height: var(--tag-height-sm); text-overflow: ellipsis; white-space: nowrap; }
.session-time { display: inline-flex; align-items: center; gap: var(--space-1); margin-top: var(--space-2); color: var(--text-secondary); font-size: var(--font-size-xs); }
.session-meta-line { display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-2); margin-top: var(--space-2); color: var(--text-secondary); font-size: var(--font-size-xs); }
.session-meta-line span { display: inline-flex; align-items: center; gap: var(--space-1); min-width: 0; }
.session-short-id { font-family: var(--font-family-number); }
.session-actions { color: var(--text-placeholder); }
.session-actions:hover { color: var(--color-danger); }
.session-empty { display: grid; min-height: 0; flex: 1; place-items: center; padding: var(--space-8) var(--space-4); color: var(--text-secondary); font-size: var(--font-size-sm); text-align: center; }
@media (max-width: 640px) {
  .session-list { min-height: 320px; height: 360px; }
}
</style>
