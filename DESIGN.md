# DESIGN.md — 前端设计系统与 UI 约束

> **地位：** 本仓库**前端（SPA）**的详细设计权威文档。  
> **不在本文范围：** 系统架构、数据/ML 协议、FastAPI 路由实现、Agent/Pi 后端逻辑 → 一律见 **`AGENTS.md`**。  
> **配套：** 范围见 `docs/plans/`；变更见 `CHANGE.md`。  
> **版本：** v0.3.0（2026-07-30）— 阶段9：9 路由；模型实验室全图化；新增预算模拟页与 Pi 编排中枢页。

---

## 0. 文档怎么用

| 你在做什么 | 读哪里 |
|------------|--------|
| 改页面、样式、组件、图表、交互文案 | **本文** |
| 改 API 字段、训练、Agent 工具、Pi 路径 | **AGENTS.md** |
| 前后端字段对不上 | 先改 AGENTS API 节，再改本文 §4「接口消费」 |

**硬规则：** 前端不得发明第二套业务指标口径；所有 AUC/转化率/SHAP 数值必须来自后端响应或后端产物接口。

---

## 1. 产品前端目标

在浏览器中提供可答辩演示的分析工作台：

1. 一眼看懂数据规模、转化分布与质量告警  
2. 对比模型指标（强调 PR-AUC，而非只秀 Accuracy）  
3. 对单客户做预测 + SHAP 解释  
4. 浏览分群画像与关联规则  
5. 与分析 Copilot 对话，并**展开 tool_trace** 证明数字有据  
6. 提供复现说明入口（链到命令与数据出处）  

**非目标（前端）：** 营销自动化编排器、复杂权限中心、移动 App、重动画营销落地页。

---

## 2. 技术栈锁定

| 项 | 选择 | 说明 |
|----|------|------|
| 框架 | **Vue 3** | Composition API + `<script setup>` 优先 |
| 构建 | **Vite** | 开发端口 **5600**（`vite.config.ts`，可配置） |
| UI 库 | **Element Plus** | 不引入第二套组件库（禁止再上 Ant/Naive 等） |
| 图表 | **ECharts**（vue-echarts 或封装组件） | 统一主题变量 |
| 路由 | Vue Router | history 模式（开发） |
| 状态 | Pinia（按需） | 勿把整表 CSV 塞进 store |
| HTTP | axios | 统一实例与 envelope 解析 |
| 语言 | TypeScript **推荐**；若初期 JS 须在 CHANGE 声明，后续可迁 | 类型与 AGENTS DTO 对齐 |
| 包管理 | npm 或 pnpm（项目内锁定一种） | lockfile 入库 |

**禁止：**

- 无评审切换 React/Svelte  
- jQuery、随意 CDN 全局污染  
- 在组件内硬编码 `localhost` 且无法用 env 覆盖  
- 为“好看”引入大型 3D/粒子库（答辩无必要）  

---

## 3. 信息架构与路由

### 3.1 站点地图

| 路由 | 名称 | 优先级 | 主要内容 |
|------|------|--------|----------|
| `/` | 总览 Dashboard | P0 | KPI、转化分布、质量告警、数据摘要 |
| `/models` | 模型实验室 | P0 | E0–E8 对比表（CV/CI/Brier）、PR/ROC、校准、混淆矩阵、lift、阈值-成本 |
| `/customers` | 客户洞察 | P0 | 查 ID/表单特征 → 概率、标签、SHAP、反事实（模型行为口径） |
| `/segments` | 分群画像 | P1 | 簇列表、自动画像名、PCA 投影、多算法对比、稳定性徽章 |
| `/rules` | 关联规则 | P1 | 规则表、Lift 筛选、免责声明 |
| `/simulate` | 预算模拟 | 阶段9 | 参数表单、期望收益曲线、推荐 K、Top 名单、CSV 导出 |
| `/agent` | AI 分析台 | P0 | 对话、runtime 徽章、五段契约、tool_trace |
| `/pi` | Pi 编排中枢 | 阶段9 | runtime 状态、skills 列表、一键报告、审计表格、会话回放 |
| `/about` | 关于与复现 | P0 | 启动命令、数据出处、AI 使用说明、链接 AGENTS |

未实现的 P1 页：导航可显示但内容为「即将推出 / 请先运行 scripts」空态，**不要**死链 404 吓退演示。

### 3.2 全局布局

```text
┌─────────────────────────────────────────────────────────────┐
│ AppHeader：项目名 | 主导航 | 健康状态点 | Agent Runtime 徽章   │
├──────────────┬──────────────────────────────────────────────┤
│ AppSider     │  PageHeader（标题 + 简短说明 + 主操作）        │
│ （可折叠）   │  ─────────────────────────────────────────   │
│ 总览         │  Content（卡片 / 分栏 / 表图）                 │
│ 模型         │                                               │
│ 客户         │                                               │
│ 分群         │                                               │
│ 规则         │                                               │
│ 预算模拟     │                                               │
│ AI 分析台    │                                               │
│ Pi 中枢      │                                               │
│ 关于         │                                               │
└──────────────┴──────────────────────────────────────────────┘
│ AppFooter（可选）：免责声明一行 + 文档链接                      │
└─────────────────────────────────────────────────────────────┘
```

- **桌面优先**（答辩投影 1366×768 及以上可完整使用）  
- `< 992px`：侧栏收为抽屉；图表允许横向滚动，不挤碎轴标签  
- 内容区最大宽建议 **1280–1440px**，居中，避免超宽拉伸  

### 3.3 用户关键路径（演示）

1. 总览确认数据与质量 →  
2. 模型页指出 PR-AUC 与 Dummy 陷阱 →  
3. 客户页解释 1 个高概率样例 →  
4. AI 台问「各渠道转化率」并展开 trace →  
5. （完整版）分群/规则快速带过  

前端须保证上述路径 **点击次数少、无阻塞弹窗连环**。

---

## 4. 接口消费约定（前端视角）

> 路径与字段权威在 **AGENTS.md §10**；本节只约束前端如何用。

### 4.1 HTTP 基础

- `baseURL`：`import.meta.env.VITE_API_BASE_URL` 或默认 `http://127.0.0.1:9800/api/v1`  
- 超时：普通 30s；`/agent/chat` 建议 120s  
- 统一解析 envelope：`ok === true` 用 `data`；否则抛出 `error.message`（中文展示）  
- 每个列表/详情请求失败：页面内 Alert，而不是白屏  

### 4.2 前端必须遵守的字段

| 场景 | 必须展示/携带 |
|------|----------------|
| 预测结果 | `proba`（建议 4 位小数）、`label`、`threshold`、`run_id` |
| 模型表 | PR-AUC、ROC-AUC；Accuracy 若展示须标注「仅对照」 |
| SHAP | `top_features` 列表；标明 `method` |
| Agent | 可见 `tool_trace`；runtime 名称；session 可续聊 |
| Pi 状态 | 仅展示后端 `/agent/pi/status` 结果；前端不扫描用户磁盘找 `pi` |

### 4.3 前端禁止

- 禁止本地用假随机数生成「演示 AUC」  
- 禁止把 API Key 写进前端 env 提交库（LLM Key 只在后端）  
- 禁止前端直接读 `data/*.csv` 当生产路径（演示样例可用后端接口或静态 fixture 经后端）  

---

## 5. 视觉设计系统

### 5.1 原则

| 原则 | 说明 |
|------|------|
| 数据产品感 | 干净、克制、偏仪表盘；少插画少装饰线 |
| 信息优先 | 数字与表格对比优先于营销风大图 |
| 一致性 | 同一语义同一颜色/字号/间距 |
| 可投影 | 对比度足够；避免过浅灰字 |
| 色盲友好 | 不只靠红绿；用形状/位置/标签辅助 |

### 5.2 颜色（CSS 变量，实现时落到 `frontend/src/styles/tokens.css`）

| Token | 用途 | 建议起点（可微调但须全站统一） |
|-------|------|--------------------------------|
| `--color-bg` | 页面背景 | 中性浅灰 `#F5F7FA` |
| `--color-surface` | 卡片背景 | `#FFFFFF` |
| `--color-border` | 边框 | `#E4E7ED` |
| `--color-text` | 主文案 | `#303133` |
| `--color-text-secondary` | 次要 | `#909399` |
| `--color-primary` | 主操作/链接 | 统一蓝系，与 Element Plus primary 对齐 |
| `--color-success` | 正向/通过 | Element success |
| `--color-warning` | 质量告警 | Element warning |
| `--color-danger` | 错误/负贡献 | Element danger |
| `--color-info` | 中性提示 | Element info |

**业务着色建议：**

- 转化率/概率：用**连续色序**（单色深浅）或蓝紫序，避免「绿=一定好」无说明  
- SHAP 正贡献 / 负贡献：两端色 + 中间 0 轴；图例写清「推向转化 / 拉低转化」  
- 质量告警：warning 标签，不与「未转化」混用同一红色语义而不加文字  

**禁止：** 每页临时选色；大面积高饱和背景；纯红底白字大块装饰。

### 5.3 字体

- 优先系统字体栈：  
  `"Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif`  
- 指标数字：`tabular-nums`（等宽数字）便于对齐  
- 字号阶梯（建议）：  
  - 页面标题 20–22px  
  - 卡片标题 16px  
  - 正文 14px  
  - 辅助 12–13px  
- 行高 1.5–1.6；不要密不透风  

### 5.4 间距与圆角

- **8px 网格**：4 / 8 / 16 / 24 / 32  
- 卡片内边距：16–20px  
- 区块间距：16–24px  
- 圆角：6–8px（与 Element 默认协调）  
- 阴影：轻微一层即可，避免多重阴影堆叠  

### 5.5 图标

- 使用 Element Plus Icons  
- 图标按钮必须有 `title` 或旁注文字（无障碍与演示友好）  
- 勿使用含义不清的纯图标导航  

### 5.6 暗色模式

- **P0 不做**；P2 可选  
- 若做：必须走 CSS 变量切换，禁止每页手写一套暗色  

---

## 6. 布局与栅格

- 使用 Element `el-row` / `el-col` 或 CSS grid  
- Dashboard：顶排 3–4 个 KPI 卡，下方 2 列「分布图 | 质量列表」  
- 模型页：上表下图或左表右说明  
- 客户页：左表单右结果（宽屏）；窄屏上下堆叠  
- AI 台：左对话主栏（≈65%）+ 右上下文/trace（≈35%）；窄屏 trace 改折叠面板  

**密度：** 默认舒适密度；表格可「中等」；不要默认用 Element 的 mini 导致投影看不清。

---

## 7. 组件规范

### 7.1 基础组件（优先 Element）

| 用途 | 组件 |
|------|------|
| 按钮 | `el-button`（主操作 primary，次要 default） |
| 表单 | `el-form` + rules；提交防抖 |
| 表格 | `el-table`；空数据 `slot empty` |
| 标签 | `el-tag` 表达状态 |
| 提示 | `el-alert` / `ElMessage` / `ElMessageBox` |
| 加载 | `v-loading` |
| 抽屉/对话框 | 复杂表单用 dialog；侧详用 drawer |

### 7.2 业务组件（建议自建）

| 组件名建议 | 职责 |
|------------|------|
| `KpiCard` | 标题、主数值、副文案、`run_id`/来源 hint |
| `PageHeaderBar` | 标题、描述、右侧 actions |
| `ModelMetricsTable` | 多模型指标；高亮主指标列 PR-AUC |
| `ShapBarChart` | 水平条形；正负双向 |
| `QualityIssueList` | 质量问题计数与说明 |
| `DisclaimerBanner` | 相关非因果固定文案 |
| `AgentMessageList` | 气泡列表 |
| `ToolTracePanel` | 工具名、参数摘要、成功/失败、耗时（折叠面板） |
| `RuntimeBadge` | pi / local / template + stub/降级原因 tooltip |
| `RocPrCurveChart` | PR / ROC 双联曲线（左 PR 右 ROC，随机基线虚线） |
| `CalibrationChart` | 校准曲线（完美对角线 + before/after 双色） |
| `ConfusionHeatmap` | 2×2 混淆矩阵热力（x=预测 y=实际） |
| `LiftChart` | 十分位 capture_rate 柱 + lift 折线（右轴） |
| `ThresholdScanChart` | P/R/F1 三线 + 期望成本右轴 + 当前/成本最优/选中三档 markLine |
| `ScatterPcaChart` | PCA 2D 散点（按簇着色 + 自动画像名图例） |
| `BudgetCurveChart` | 期望净收益/毛收益/转化数曲线 + 推荐 K markLine |
| `CounterfactualCurveChart` | 单特征扰动 proba 曲线 + 当前样本点 + 目标线 |
| `EmptyState` | 无数据时引导运行后端脚本 |
| `ErrorState` | 展示后端 `error.message` + 重试 |

### 7.3 KPI 卡规则

- 主数字最大最重  
- 副标题说明指标含义（如「测试集 PR-AUC」）  
- 若有对比，写清对比对象（vs Dummy）  
- 加载时用骨架屏，避免数字从 0 跳动误导  

### 7.4 表格规则

- 概率/AUC：**4 位小数**  
- 转化率：百分比 **2 位**（如 87.65%）  
- 大整数：千分位  
- 长 ID：可复制按钮  
- 默认不关边框到「看不清行」  

### 7.5 表单规则

- 标签中文；placeholder 给示例而非再复述标签  
- 数字输入限制范围（与 schema 提示一致，若后端返回 meta 则用 meta）  
- 主按钮「预测 / 发送」在表单可视区内；提交中 disable 防连点  

---

## 8. 图表规范（ECharts）

### 8.1 通用

- 每图必有：**标题**（或卡片标题）、**图例**（多系列时）、轴名称（若适用）  
- 配色从 token 派生，不写死一堆随机 hex  
- tooltip 中文；数值格式与表格一致  
- 动画：默认轻量；`prefers-reduced-motion` 时可关  
- 容器须设明确高度（如 320–400px），禁止高度 0  

### 8.2 推荐图表类型

| 页面 | 图表 | 备注 |
|------|------|------|
| 总览 | 转化 0/1 占比饼/环；渠道柱状 | 饼图类别 ≤5；多类改条形 |
| 模型 | PR/ROC 双联曲线；校准曲线；混淆热力；lift 柱+折线；阈值-成本多线 | run 下拉切换；阈值滑块联动 |
| 客户 | SHAP 水平条；反事实单特征曲线 | 按绝对值排序可切换 |
| 分群 | PCA 2D 散点；簇大小柱状；多算法对比表 | 雷达维数 ≤8 |
| 规则 | 一般用表；Lift 可用条形 | 避免强行 3D |
| 模拟 | 期望收益曲线（净/毛/转化数） | 推荐 K markLine |

图表颜色统一从 `utils/chartTheme.ts` 常量派生（与 tokens.css 对齐），禁止组件内散落硬编码 hex。

### 8.3 禁止

- 无意义 3D 饼图  
- 双 Y 轴故意夸大差异却不说明  
- 堆叠面积图信息过载却无筛选  

---

## 9. 文案、语气与免责声明

### 9.1 语气

- 专业、简洁、本科答辩友好  
- 少用「赋能」「打造闭环」等空话  
- 错误提示说明「现象 + 可尝试动作」（如：模型未加载，请先运行 `python scripts/run_all.py`）  

### 9.2 固定免责声明（须在分群、规则、Agent、策略建议附近可见）

> 以下洞察基于历史数据中的**相关关系**与模型估计，**不构成因果证明**，也不构成实际投放收益承诺。

### 9.3 指标命名展示

| 内部字段 | UI 展示名 |
|----------|-----------|
| pr_auc | PR-AUC |
| roc_auc | ROC-AUC |
| f1 | F1 |
| accuracy | Accuracy（仅对照） |
| proba | 转化概率 |

---

## 10. 页面级详细约束

### 10.1 总览 `/`

**必须有：**

- 样本量、正/负样本数或转化率  
- 质量问题条数入口（可点到说明）  
- 至少 1 个分布图（渠道或转化）  
- 后端未就绪时的 EmptyState  

**不要：** 无数据时假装已有漂亮假图。

### 10.2 模型实验室 `/models`

**必须有：**

- E0–E8 对比表，**PR-AUC 列优先高亮**；Dummy 行 tag；**E5/E6 消融行标「消融·不作默认」**  
- 列：PR-AUC、CV 5-fold 均值±std、95% CI（bootstrap）、ROC-AUC、F1、Brier、Accuracy（仅对照）、阈值  
- run 下拉联动：PR/ROC 双联曲线、混淆矩阵热力、lift 图  
- 阈值-成本分析：多线图 + 滑块联动 P/R/F1/期望成本（当前/成本最优/选中三档 markLine）  
- 校准曲线（E8）：完美对角线 + before/after 双色  
- 全局 SHAP 条形  
- 顶部口径文案：CI 重叠不宣称更优；消融不参选默认  

### 10.3 客户洞察 `/customers`

**必须有：**

- 输入：CustomerID **或** 特征表单（二选一主路径，另一可次要）  
- 输出：概率、标签、阈值、run_id  
- SHAP Top 特征图或表  
- 预置「样例填充」按钮（答辩用，数据来自后端或约定 fixture）  
- **反事实面板：** 扰动特征下拉（数值列）+ 目标 proba → 单特征 proba 曲线（当前样本点 + 目标线）+ 达标步骤表（特征/from/to/proba_after）+ 强制 disclaimer（模型行为口径，非因果非投放建议）  
- 批量预测（上限 200）  

### 10.4 分群 `/segments`

- 簇表：ID、**自动画像名**、占比、事后转化率、3–5 个显著特征  
- **稳定性徽章：** bootstrap ARI 均值±std（≥0.75 绿 / ≥0.5 蓝 / 否则黄）  
- PCA 2D 散点（按簇着色，图例带自动画像名）  
- 多算法对比表（KMeans/GMM/Agglomerative × K；silhouette/CH/BIC；当前主分群行高亮）  
- 策略文案区必须带免责声明  
- 无产物：EmptyState 提示跑分群脚本  

### 10.5 规则 `/rules`

- 表列：前件、后件、support、confidence、lift  
- 可按 lift 排序/筛选  
- 顶部免责声明  

### 10.6 AI 分析台 `/agent`

**必须有：**

- 多轮消息列表  
- 发送框 + 加载中状态  
- **Runtime 展示与切换**（默认 pi；切换调后端，失败提示；stub/降级显示原因）  
- 每条助手消息可展开 **tool_trace**（ToolTracePanel 组件）  
- **五段契约完整渲染：** observed_facts / inferences / recommendations / open_questions / tool_trace  
- `pi_fallback=true` 时显示「Pi 降级」警告 tag  
- 建议「示例问题」chips（含实验对比/校准/预算/反事实新工具例）降低冷启动  

**交互细节：**

- Enter 发送，Shift+Enter 换行（若多行输入）  
- 失败消息可「重试」  
- 不在前端渲染未转义的危险 HTML（markdown 若启用须消毒）  

### 10.7 关于 `/about`

- 复现命令（与 AGENTS 一致）  
- 数据来源链接/说明  
- 文档入口：`AGENTS.md` / 本文件 / 计划书路径说明  
- AI 使用说明摘要（毕设诚信）  

### 10.8 预算模拟 `/simulate`

**必须有：**

- 参数表单：单客转化价值、单次触达成本、预算上限（可空）+ 盈亏平衡 proba 回显  
- KPI 行：推荐 K、期望净收益、期望转化数、评估人群（test n + run_id）  
- 期望收益曲线（BudgetCurveChart：净收益主线 + 毛收益/转化数虚线 + 推荐 K markLine）  
- Top 名单预览表（≤50：rank/CustomerID/proba/期望价值）+ 「导出名单 CSV」按钮（显示落盘路径）  
- 固定 disclaimer：期望值口径，非因果收益承诺  

### 10.9 Pi 编排中枢 `/pi`

**必须有：**

- Runtime 状态卡：默认 runtime、可执行文件、stub/真实安装 tag、降级原因、会话数（RuntimeBadge）  
- Skills 列表（名称 + 描述，来自 `/agent/pi/status` 的 skills_detail）  
- 一键报告：标题输入 + 生成按钮 → n_sections_ok/n_sections、落盘路径、digest 预览、tool_trace  
- 审计表格（最近 N 条：时间/runtime/用户消息/工具/会话/耗时）  
- 会话回放：输入 session_id → 展示完整会话 JSON  
- 口径文案：Pi 仅 `tools/pi-cli/`，禁止全局回退  

---

## 11. 交互与反馈

| 场景 | 行为 |
|------|------|
| 加载 > 300ms | 显示 loading |
| 成功轻操作 | Message 成功（自动关闭） |
| 破坏性 | 本系统少见；若有删除须确认 |
| 表单校验失败 | 定位到首个错误字段 |
| 会话丢失 | Agent 可新开 session，提示旧会话不可用 |
| 快捷键 | 不做复杂全局快捷键（P0） |

**动效：** 页面切换可用轻 fade；避免长动画耽误演示。

---

## 12. 无障碍与国际化

- 对比度：正文与背景达到可读（避免浅灰上浅灰）  
- 焦点可见：键盘可点主按钮  
- 图表不只依赖颜色传达唯一信息  
- **语言：仅简体中文**（P0 不做 i18n 框架）  
- 图标按钮补充文案或 `aria-label`  

---

## 13. 前端工程结构（建议）

```text
frontend/
  index.html
  package.json
  vite.config.ts
  .env.example                 # VITE_API_BASE_URL=
  src/
    main.ts
    App.vue
    styles/
      tokens.css
      index.css
    router/index.ts
    stores/                    # app, metrics, agent...
    api/                       # axios 实例与各模块 API
    components/                # 通用与业务组件
    views/                     # 页面级
    utils/                     # 格式化、envelope
    assets/
```

**约定：**

- `views` 不写复杂请求细节，放 `api/`  
- 格式化函数集中（`formatPercent`、`formatAuc`）  
- 禁止循环依赖：`components` 不依赖 `views`  

---

## 14. 状态管理

| Store | 内容 |
|-------|------|
| `app` | health、版本、runtime、侧栏折叠 |
| `metrics` | 缓存的模型对比；注意失效刷新 |
| `agent` | session_id、messages、pending、最后 error |

**原则：** 服务器为真相来源；刷新页面后可重新拉取；Agent 消息可 sessionStorage 可选缓存（P2）。

---

## 15. 性能

- 路由级懒加载页面  
- ECharts 按需引入或统一 chart 封装，避免重复初始化泄漏  
- 大表分页（规则列表）  
- 图片资源尽量无（本项目以图为主数据可视化）  
- 开发环境 source map 可开；提交前注意包体体积不必过度优化  

---

## 16. 安全（前端侧）

- 不存储 API Key  
- 不使用 `v-html` 渲染 Agent 原始输出（除非消毒）  
- 外链 `rel="noopener"`  
- 环境变量仅 `VITE_*` 非机密配置  

---

## 17. 空态 / 错态 / 加载 文案示例

| 状态 | 示例文案 |
|------|----------|
| 模型未加载 | 尚未找到模型产物。请在项目根运行 `python scripts/run_all.py` 后刷新。 |
| 分群缺失 | 分群结果未生成。请运行分群脚本或完整流水线。 |
| Agent 无 Key 降级 | 当前为模板模式：仍可调用分析工具，但自然语言编排能力有限。 |
| Pi 未安装 | 项目内 Pi CLI 未就绪。请运行 `python scripts/setup_pi_cli.py`（不会使用你电脑上的全局 pi）。 |
| 网络失败 | 无法连接后端，请确认 API 已在 :9800 启动。 |

---

## 18. 与后端联调检查清单

```text
□ VITE_API_BASE_URL 指向正确
□ /health 绿点
□ 总览数字与 /data/overview 一致
□ 模型表 PR-AUC 与 /models/metrics 一致
□ 预测展示 threshold 与 run_id
□ SHAP 条与 top_features 一致
□ Agent 能展开 tool_trace
□ Runtime 切换失败有中文原因
□ 免责声明出现在分群/规则/Agent
□ 无 Key 时页面不白屏
```

---

## 19. 设计变更流程

1. 改路由/视觉 token/组件契约 → 更新本文版本与对应节  
2. 追加 `CHANGE.md`  
3. 若影响后端字段 → 同步 `AGENTS.md` API 节  
4. 再改 `frontend/` 代码  

---

## 20. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-30 | 初版（含全栈设计，已废止该形态） |
| v0.2.0 | 2026-07-30 | **收窄为前端专用**；架构/后端迁入 AGENTS.md |
| v0.3.0 | 2026-07-30 | 阶段9：9 路由（+`/simulate` `/pi`）；模型实验室全图化（CV/CI/Brier 列 + 5 类评估图 + 校准）；客户页反事实；分群页对比/投影/稳定性；Agent 五段渲染 + RuntimeBadge/ToolTracePanel 组件化；chartTheme 统一图表色 |

---

**一句话：** `DESIGN.md` 管「看起来与点起来是否一致、专业、可演示」；「算得对不对、架构合不合理」以 `AGENTS.md` 为准。
