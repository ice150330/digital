<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fetchHealth, type HealthData } from '../api/health'

const route = useRoute()
const health = ref<HealthData | null>(null)
const healthError = ref<string | null>(null)
const loading = ref(true)

const nav = [
  { to: '/', label: '总览' },
  { to: '/models', label: '模型实验室' },
  { to: '/customers', label: '客户洞察' },
  { to: '/segments', label: '分群画像' },
  { to: '/rules', label: '关联规则' },
  { to: '/agent', label: 'AI 分析台' },
  { to: '/about', label: '关于与复现' },
]

const statusColor = computed(() => {
  if (healthError.value) return '#F56C6C'
  if (health.value?.status === 'ok') return '#67C23A'
  if (health.value?.status === 'degraded') return '#E6A23C'
  return '#909399'
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
      <aside class="sider">
        <div class="nav-title">导航</div>
        <router-link
          v-for="item in nav"
          :key="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
          :to="item.to"
        >
          {{ item.label }}
        </router-link>
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
  background: #ecf5ff;
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
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}
.nav-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  padding: 4px 12px 8px;
}
.nav-item {
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--color-text);
  text-decoration: none;
}
.nav-item.active {
  background: #ecf5ff;
  color: var(--color-primary);
  font-weight: 600;
}
.nav-item:hover:not(.active) {
  background: #f5f7fa;
}
.main {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
@media (max-width: 992px) {
  .sider {
    width: 160px;
  }
}
</style>
