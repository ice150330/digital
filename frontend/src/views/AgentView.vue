<script setup lang="ts">
import EmptyState from '../components/EmptyState.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="AI 分析台"
      description="工具接地 Copilot：数字来自工具结果，须展示 tool_trace。"
    />
    <p class="disclaimer">LLM 不替代主分类器；无工具结果时不得编造 PR-AUC / 转化率等数字。</p>
    <EmptyState
      title="Agent 即将接入"
      description="阶段 5 将提供 POST /agent/chat、LocalToolRuntime 与 tool_trace 面板。"
    />
  </div>
</template>
