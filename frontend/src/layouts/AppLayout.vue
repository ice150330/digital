<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchHealth, type HealthData } from '../api/health'

const health = ref<HealthData | null>(null)
const healthError = ref<string | null>(null)
const loading = ref(true)

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
        <span class="health" :title="healthError || health?.message || ''">
          <span class="dot" :style="{ background: statusColor }" />
          {{ statusText }}
        </span>
      </div>
    </header>
    <div class="body">
      <aside class="sider">
        <div class="nav-title">导航</div>
        <router-link class="nav-item active" to="/">总览</router-link>
        <div class="nav-item disabled">模型实验室</div>
        <div class="nav-item disabled">客户洞察</div>
        <div class="nav-item disabled">分群画像</div>
        <div class="nav-item disabled">关联规则</div>
        <div class="nav-item disabled">AI 分析台</div>
        <div class="nav-item disabled">关于与复现</div>
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
  background: #f5f7fa;
  color: #303133;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.header {
  height: 56px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
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
  color: #909399;
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
  width: 200px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-title {
  font-size: 11px;
  font-weight: 600;
  color: #909399;
  padding: 4px 12px 8px;
}
.nav-item {
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #303133;
  text-decoration: none;
}
.nav-item.active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}
.nav-item.disabled {
  color: #c0c4cc;
  cursor: not-allowed;
}
.main {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
</style>
