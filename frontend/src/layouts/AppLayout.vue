<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChatDotRound,
  Coin,
  Collection,
  Connection,
  DataBoard,
  Expand,
  Fold,
  Histogram,
  InfoFilled,
  Odometer,
  Operation,
  User,
} from '@element-plus/icons-vue'
import { fetchHealth, type HealthData } from '../api/health'

const route = useRoute()
const health = ref<HealthData | null>(null)
const healthError = ref<string | null>(null)
const loading = ref(true)
const collapsed = ref(false)

// Stage 6：侧栏四层叙事分组 —— 数据分析 → 数据挖掘 由浅入深
const navSections = [
  {
    title: '总览大屏',
    items: [{ to: '/screen', label: '总览大屏', icon: DataBoard }],
  },
  {
    title: '描述性分析',
    items: [{ to: '/', label: '数据总览', icon: Odometer }],
  },
  {
    title: '预测建模',
    items: [
      { to: '/models', label: '模型实验室', icon: Histogram },
      { to: '/customers', label: '客户洞察', icon: User },
    ],
  },
  {
    title: '深度挖掘',
    items: [
      { to: '/segments', label: '分群画像', icon: Collection },
      { to: '/rules', label: '关联规则', icon: Connection },
      { to: '/simulate', label: '预算模拟', icon: Coin },
    ],
  },
  {
    title: 'AI 与系统',
    items: [
      { to: '/agent', label: 'AI 分析台', icon: ChatDotRound },
      { to: '/pi', label: 'Pi 编排中枢', icon: Operation },
      { to: '/about', label: '关于与复现', icon: InfoFilled },
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

async function refreshHealth() {
  loading.value = true
  healthError.value = null
  try {
    const { data } = await fetchHealth()
    health.value = data
  } catch (e) {
    health.value = null
    healthError.value = e instanceof Error ? e.message : '未知错误'
  } finally {
    loading.value = false
  }
}

onMounted(refreshHealth)
defineExpose({ refreshHealth, health })
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="brand">营销转化分析</div>
      <div class="header-right">
        <span
          v-if="health?.default_run_id"
          class="run-chip mono"
          :title="health.artifacts_ok ? '产物就绪' : '产物降级'"
        >
          {{ health.default_run_id }}
        </span>
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
          @click="collapsed = !collapsed"
        >
          <el-icon><Expand v-if="collapsed" /><Fold v-else /></el-icon>
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
            <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
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
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
}
.header {
  height: var(--header-height);
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.brand {
  font-weight: 700;
  font-size: 16px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.run-chip {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 11px;
}
.health {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.body {
  flex: 1;
  display: flex;
  min-height: 0;
}
.sider {
  width: var(--sider-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
  transition: width 0.18s ease;
  overflow: hidden;
}
.sider.collapsed {
  width: 64px;
}
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  margin-bottom: 6px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.15s ease;
}
.collapse-btn:hover {
  background: var(--color-hover);
  color: var(--color-primary);
}
.nav-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  padding: 10px 12px 4px;
  letter-spacing: 1px;
  white-space: nowrap;
}
.nav-divider {
  height: 1px;
  margin: 8px 10px 4px;
  background: var(--color-border);
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--color-text);
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease;
}
.nav-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.nav-item.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}
.nav-item:hover:not(.active) {
  background: var(--color-hover);
}
.sider.collapsed .nav-item {
  justify-content: center;
  padding: 9px 0;
}
.main {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
@media (max-width: 992px) {
  .sider {
    width: 64px;
  }
  .sider .nav-label,
  .sider .nav-title {
    display: none;
  }
  .sider .nav-item {
    justify-content: center;
    padding: 9px 0;
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
