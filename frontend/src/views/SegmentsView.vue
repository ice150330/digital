<script setup lang="ts">
import EmptyState from '../components/EmptyState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="分群画像"
      description="P1：K-Means 等分群；训练特征不含 Conversion，事后看簇转化率。"
    />
    <p class="disclaimer">分群用于探索画像，簇间转化率差异<strong>不等于</strong>因果效应。</p>
    <EmptyState
      title="分群尚未就绪"
      description="阶段 6 将提供 scripts/03_train_cluster.py 与 GET /segments。导航可进入本页，避免 404。"
    />
  </div>
</template>
