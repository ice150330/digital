<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import Icon from '../components/Icon.vue'
import RunIdChip from '../components/RunIdChip.vue'
import { useHealth } from '../composables/useHealth'
import { useAppStore } from '../stores/app'

const route = useRoute()
const appStore = useAppStore()
const { sidebarCollapsed: collapsed } = storeToRefs(appStore)
const { health, healthError, healthLoading: loading, refreshHealth } = useHealth()

// Stage 6：侧栏四层叙事分组 —— 数据分析 → 数据挖掘 由浅入深
const navSections = [
  {
    title: '总览大屏',
    items: [{ to: '/screen', label: '总览大屏', icon: 'uil:desktop-alt' }],
  },
  {
    title: '描述性分析',
    items: [{ to: '/', label: '数据总览', icon: 'uil:apps' }],
  },
  {
    title: '预测建模',
    items: [
      { to: '/models', label: '模型实验室', icon: 'uil:chart' },
      { to: '/customers', label: '客户洞察', icon: 'uil:user' },
    ],
  },
  {
    title: '深度挖掘',
    items: [
      { to: '/segments', label: '分群画像', icon: 'uil:users-alt' },
      { to: '/rules', label: '关联规则', icon: 'uil:code-branch' },
      { to: '/simulate', label: '预算模拟', icon: 'uil:wallet' },
    ],
  },
  {
    title: 'AI 与系统',
    items: [
      { to: '/agent', label: 'AI 分析台', icon: 'uil:comment-dots' },
      { to: '/pi', label: 'Pi 编排中枢', icon: 'uil:cog' },
      { to: '/about', label: '关于与复现', icon: 'uil:info-circle' },
    ],
  },
]

const statusColor = computed(() => {
  if (healthError.value) return 'var(--color-danger)'
  if (health.value?.status === 'ok') return 'var(--color-success)'
  if (health.value?.status === 'degraded') return 'var(--color-warning)'
  return 'var(--color-info)'
})

const statusText = computed(() => {
  if (loading.value) return '检查中…'
  if (healthError.value) return 'API 不可达'
  if (health.value?.status === 'ok') return 'API 健康'
  if (health.value?.status === 'degraded') return 'API 降级'
  return '未知'
})

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

defineExpose({ refreshHealth, health })
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="brand">营销转化分析</div>
      <div class="header-right">
        <RunIdChip
          v-if="health?.default_run_id"
          :value="health.default_run_id"
          :title="health.artifacts_ok ? '产物就绪' : '产物降级'"
        />
        <span class="health" :title="healthError || health?.message || ''">
          <span class="dot" :style="{ background: statusColor }" />
          {{ statusText }}
        </span>
      </div>
    </header>
    <div class="body">
      <aside class="sider" :class="{ collapsed }">
        <button
          class="collapse-btn"
          :title="collapsed ? '展开侧栏' : '收起侧栏'"
          @click="appStore.toggleSidebar"
        >
          <Icon :icon="collapsed ? 'uil:angle-right' : 'uil:angle-left'" size="md" :title="collapsed ? '展开侧栏' : '收起侧栏'" />
        </button>
        <nav v-for="section in navSections" :key="section.title" class="nav-section">
          <div v-if="!collapsed" class="nav-title">{{ section.title }}</div>
          <div v-else class="nav-divider" />
          <router-link
            v-for="item in section.items"
            :key="item.to"
            class="nav-item"
            :class="{ active: isActive(item.to) }"
            :to="item.to"
            :title="item.label"
          >
            <Icon class="nav-icon" :icon="item.icon" size="md" :title="item.label" />
            <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
          </router-link>
        </nav>
      </aside>
      <main class="main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
  color: var(--text-body);
  font-family: var(--font-family-base);
}
.header {
  height: var(--layout-header-height);
  padding: 0 var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-default);
}
.brand {
  color: var(--text-title);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-lg);
}
.header-right {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.health {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}
.dot {
  width: var(--space-2);
  height: var(--space-2);
  border-radius: var(--radius-full);
  display: inline-block;
}
.body {
  flex: 1;
  display: flex;
  min-height: 0;
  max-width: 100vw;
  overflow-x: hidden;
}
.sider {
  width: var(--layout-sidebar-width);
  background: var(--bg-card);
  border-right: 1px solid var(--border-default);
  padding: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex-shrink: 0;
  transition: width var(--motion-duration-base) var(--motion-easing-default);
  overflow: hidden;
}
.sider.collapsed {
  width: var(--layout-sidebar-collapsed);
}
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: var(--space-8);
  margin-bottom: var(--space-2);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background var(--motion-duration-fast) var(--motion-easing-default), color var(--motion-duration-fast) var(--motion-easing-default);
}
.collapse-btn:hover {
  background: var(--bg-subtle);
  color: var(--color-primary-600);
}
.nav-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.nav-title {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
  padding: var(--space-3) var(--space-3) var(--space-1);
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.nav-divider {
  height: 1px;
  margin: var(--space-2) var(--space-2) var(--space-1);
  background: var(--border-default);
}
.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--text-body);
  text-decoration: none;
  white-space: nowrap;
  transition: background var(--motion-duration-fast) var(--motion-easing-default), color var(--motion-duration-fast) var(--motion-easing-default);
}
.nav-icon {
  width: var(--space-5);
  height: var(--space-5);
  flex-shrink: 0;
}
.nav-item.active {
  background: var(--color-primary-50);
  color: var(--color-primary-700);
  font-weight: var(--font-weight-semibold);
}
.nav-item:hover:not(.active) {
  background: var(--bg-subtle);
}
.sider.collapsed .nav-item {
  justify-content: center;
  padding: var(--space-2) 0;
}
.main {
  min-width: 0;
  flex: 1;
  padding: var(--layout-page-padding);
  overflow: auto;
}
@media (max-width: 992px) {
  .sider {
    width: var(--layout-sidebar-collapsed);
  }
  .sider .nav-label,
  .sider .nav-title {
    display: none;
  }
  .sider .nav-item {
    justify-content: center;
    padding: var(--space-2) 0;
  }
}
@media (max-width: 640px) {
  .header {
    padding: 0 var(--space-3);
  }
  .brand {
    font-size: var(--font-size-md);
  }
  .health {
    display: none;
  }
  .header-right {
    min-width: 0;
    max-width: 55%;
    justify-content: flex-end;
    overflow: hidden;
  }
  .header-right :deep(.run-chip) {
    max-width: 128px;
    min-width: 0;
  }
  .main {
    width: calc(100vw - var(--layout-sidebar-collapsed));
    max-width: calc(100vw - var(--layout-sidebar-collapsed));
    flex: 0 0 calc(100vw - var(--layout-sidebar-collapsed));
    padding: var(--space-3);
    overflow-x: hidden;
  }
}
@media (max-width: 520px) {
  .header-right {
    display: none;
  }
  .sider {
    display: none;
  }
  .main {
    width: 100vw;
    max-width: 100vw;
    flex-basis: 100vw;
  }
}
@media (prefers-reduced-motion: reduce) {
  .sider,
  .collapse-btn,
  .nav-item {
    transition: none;
  }
}
</style>
