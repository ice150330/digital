<script setup lang="ts">
import EmptyState from '../components/EmptyState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="关联规则"
      description="P1：分箱 + 关联规则挖掘；展示 support / confidence / lift。"
    />
    <p class="disclaimer">关联规则表达的是<strong>相关</strong>而非因果，不可直接当作投放因果结论。</p>
    <EmptyState
      title="规则尚未就绪"
      description="阶段 6 将提供 scripts/04_mine_rules.py 与 GET /rules。"
    />
  </div>
</template>
