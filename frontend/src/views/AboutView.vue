<script setup lang="ts">
import { ElCard, ElLink } from 'element-plus'
import PageHeaderBar from '../components/PageHeaderBar.vue'
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="关于与复现"
      description="本科毕设：数字营销转化分析 + 工具接地 AI Copilot。指标与解释均来自可复现产物。"
    />

    <ElCard shadow="never" class="section-card">
      <template #header>从零复现（后端）</template>
      <pre class="code">pip install -e ".[dev]"
python scripts/init_db.py
python scripts/import_campaigns.py
python scripts/run_all.py
python scripts/run_all.py --with-p1
python scripts/export_paper_tables.py
# 或分步：01_clean → 02_train → 03_explain → 04_cluster → 05_rules
uvicorn digital_marketing.api.main:app --reload --port 9800</pre>
    </ElCard>

    <ElCard shadow="never" class="section-card">
      <template #header>前端</template>
      <pre class="code">cd frontend
npm install
npm run dev
# 开发端口 5600（vite.config.ts）</pre>
      <p class="muted">
        baseURL 使用 <code>VITE_API_BASE_URL</code>，默认
        <code>http://127.0.0.1:9800/api/v1</code>。演示清单见
        <code>scripts/demo_checklist.md</code>。
      </p>
    </ElCard>

    <ElCard shadow="never" class="section-card">
      <template #header>数据与红线</template>
      <ul class="list">
        <li>原始 CSV 只读：<code>data/digital_marketing_campaign_dataset.csv</code></li>
        <li>主数据轨：<code>outputs/db/app.db</code>（可重建）</li>
        <li>产物轨：models / metrics / explain（文件，不进 SQLite）</li>
        <li><strong>CustomerID 永不入模</strong>；主模型默认不含 ConversionRate</li>
        <li>主指标：PR-AUC（Accuracy 仅对照 + Dummy）</li>
      </ul>
    </ElCard>

    <ElCard shadow="never" class="section-card">
      <template #header>文档</template>
      <ul class="list">
        <li>架构 / 后端 / Agent：仓库根 <code>AGENTS.md</code></li>
        <li>前端设计：<code>DESIGN.md</code></li>
        <li>变更：<code>CHANGE.md</code></li>
        <li>计划：<code>docs/plans/</code></li>
      </ul>
      <p class="disclaimer" style="margin-top: 12px">
        AI 使用说明：本仓库允许使用 Claude Code 等辅助实现；论文中的数字必须以
        <code>outputs/metrics</code> 为准，禁止手改 metrics 充表。Agent 须工具接地，不得无依据编造 AUC。
      </p>
    </ElCard>

    <p class="muted">
      许可见仓库 LICENSE。远程仓库：
      <ElLink type="primary" href="https://github.com/ice150330/digital" target="_blank">
        github.com/ice150330/digital
      </ElLink>
    </p>
  </div>
</template>

<style scoped>
.code {
  margin: 0;
  padding: 12px 14px;
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 8px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  overflow: auto;
}
.list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.9;
}
</style>
