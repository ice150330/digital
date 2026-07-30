<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElAlert, ElButton, ElCard, ElDescriptions, ElDescriptionsItem, ElSkeleton } from 'element-plus'
import { fetchHealth, type HealthData } from '../api/health'

const loading = ref(true)
const error = ref<string | null>(null)
const health = ref<HealthData | null>(null)
const requestId = ref<string>('')

async function load() {
  loading.value = true
  error.value = null
  try {
    const res = await fetchHealth()
    health.value = res.data
    requestId.value = res.requestId
  } catch (e) {
    health.value = null
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>总览 · 脚手架</h1>
        <p class="desc">第一步：框架搭建与 SQLite 初始化。后续将接入 KPI / 模型 / Agent。</p>
      </div>
      <ElButton type="primary" :loading="loading" @click="load">刷新 health</ElButton>
    </div>

    <ElSkeleton v-if="loading" :rows="4" animated />

    <ElAlert
      v-else-if="error"
      type="error"
      show-icon
      :closable="false"
      title="无法连接后端"
      :description="error + '。请先启动：uvicorn digital_marketing.api.main:app --reload --port 8000'"
    />

    <ElCard v-else shadow="never" class="card">
      <template #header>
        <span>GET /api/v1/health</span>
      </template>
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem label="status">{{ health?.status }}</ElDescriptionsItem>
        <ElDescriptionsItem label="database_ok">{{ health?.database_ok }}</ElDescriptionsItem>
        <ElDescriptionsItem label="campaigns_count">{{ health?.campaigns_count }}</ElDescriptionsItem>
        <ElDescriptionsItem label="version">{{ health?.version }}</ElDescriptionsItem>
        <ElDescriptionsItem label="app">{{ health?.app }}</ElDescriptionsItem>
        <ElDescriptionsItem label="request_id">{{ requestId }}</ElDescriptionsItem>
        <ElDescriptionsItem v-if="health?.message" label="message" :span="2">
          {{ health.message }}
        </ElDescriptionsItem>
      </ElDescriptions>
      <p class="hint">
        主数据轨：CSV → <code>outputs/db/app.db</code>。分析产物轨（训练/metrics）仍写
        <code>outputs/</code> 文件，本步未启用。
      </p>
    </ElCard>
  </div>
</template>

<style scoped>
.page {
  max-width: 960px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}
h1 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
}
.desc {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.card {
  border-radius: 8px;
}
.hint {
  margin: 16px 0 0;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}
code {
  font-family: 'IBM Plex Mono', Consolas, monospace;
  font-size: 12px;
  background: #f5f7fa;
  padding: 1px 4px;
  border-radius: 3px;
}
</style>
