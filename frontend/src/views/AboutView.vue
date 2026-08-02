<script setup lang="ts">
import { ElCard, ElLink } from 'element-plus'
import CodeBlock from '../components/CodeBlock.vue'
import DisclaimerBanner from '../components/DisclaimerBanner.vue'
import PageHeaderBar from '../components/PageHeaderBar.vue'

const backendCommands = `pip install -e ".[dev]"
python scripts/init_db.py
python scripts/import_campaigns.py
python scripts/run_all.py
python scripts/run_all.py --with-p1
python scripts/export_paper_tables.py
uvicorn digital_marketing.api.main:app --reload --port 9800`

const frontendCommands = `cd frontend
npm install
npm run dev`
</script>

<template>
  <div class="page">
    <PageHeaderBar
      title="关于与复现"
      description="本科毕设：数字营销转化分析 + 工具接地 AI Copilot。指标与解释均来自可复现产物。"
    />

    <ElCard shadow="never" class="section-card">
      <template #header>从零复现（后端）</template>
      <CodeBlock :code="backendCommands" label="PowerShell · 后端复现" />
    </ElCard>

    <ElCard shadow="never" class="section-card">
      <template #header>前端</template>
      <CodeBlock :code="frontendCommands" label="PowerShell · 前端开发" />
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
      <DisclaimerBanner content="AI 使用说明：论文中的数字必须以 outputs/metrics 为准，禁止手改 metrics 充表。Agent 须工具接地，不得无依据编造 AUC。" />
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
.list {
  margin: 0;
  padding-left: var(--space-5);
  font-size: var(--font-size-sm);
  line-height: 1.9;
}
</style>
