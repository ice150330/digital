# DESIGN.md — Halo v2 前端设计系统与 UI 约束

> **地位：** 本仓库前端（Vue SPA）的视觉、页面、组件、图表与交互权威文档。
> **不在本文范围：** 系统架构、数据/ML、FastAPI、Agent/Pi 后端逻辑，统一见 `AGENTS.md`。
> **配套文件：** 范围见 `docs/plans/`；变更见 `CHANGE.md`；视觉参考库见 `pen/ui.pen`。
> **令牌源：** `docs/plans/Design Tokens.md` v2.0；运行时实现为 `frontend/src/styles/tokens.css`。
> **版本：** v0.11.1（2026-08-02）— AI 分析台消息支持 Markdown 完整样式、五段契约默认折叠、会话列表信息增强并改为组件内滚动；Halo 浅色圆角工作台、`/screen` 桑基图与 `/pi` 配置中枢保持。

---

## 0. 使用方式

| 你在做什么 | 读哪里 |
|------------|--------|
| 改颜色、字号、间距、圆角、阴影 | §6 与 `frontend/src/styles/tokens.css` |
| 改页面结构、组件、图表、交互 | §3–§12 |
| 改视觉稿 | 先看 `pen/ui.pen` 的三个画布：Design Tokens、Component Library、`/screen` |
| 改 API 字段或后端口径 | `AGENTS.md` §10；必要时同步本文 §5 |
| 改范围、分期、验收 | `docs/plans/2026-08-02-Halo风格全量视觉改造计划.md` |

**硬规则：**

1. 前端不得自造 AUC、转化率、SHAP、预算收益等数字；所有业务数字来自 `/api/v1` 或后端产物接口。
2. 新增样式必须优先使用语义 token：`--bg-*`、`--text-*`、`--border-*`、`--radius-*`、`--chart-*`。
3. `/screen` 不再是独立全屏暗色页，必须运行在 `AppLayout` 内，默认浅色。
4. `pen/ui.pen` 是前端视觉参考库；修改 UI 时需要同步对应画布或在 CHANGE 中说明未同步原因。

---

## 1. 产品前端目标

digital 前端是答辩可演示的数据分析工作台，风格定调为 **Halo 浅色 · 圆角卡片 · 中央图表叙事 · 工具接地**。它不是营销落地页，也不是纯聊天壳。

核心体验：

1. 首页快速看懂数据规模、转化占比、渠道表现和质量告警。
2. 模型页突出 PR-AUC、ROC-AUC、校准、阈值和 Dummy 对照。
3. 客户页支持单客预测、SHAP 解释和反事实敏感性分析。
4. 分群、规则、模拟页承接数据挖掘结论，但不宣称因果收益。
5. Agent 页展示真实上游 AI 回复、Markdown 消息、默认折叠的五段契约、tool_trace、会话、运行阶段和内联 chart-spec 图表。
6. `/screen` 作为开场全景：一个重点“唬人”的中央渠道转化桑基图在视觉中心，外围一圈较小图表串起转化、渠道、质量、阶段、划分和默认产物。

---

## 2. 技术栈锁定

| 项 | 选择 | 说明 |
|----|------|------|
| 框架 | Vue 3 | Composition API + `<script setup>` |
| 构建 | Vite | 前端开发端口 5600 |
| UI 库 | Element Plus | 只作为基础控件，主题由 tokens 覆盖 |
| 图标 | Iconify | 统一经 `frontend/src/components/Icon.vue` |
| 图表 | ECharts | 统一经 `BaseChart` 和 `chartTheme.ts` |
| 路由 | Vue Router | 所有页面进入 `AppLayout` |
| 状态 | Pinia | Agent 会话等跨组件状态 |
| HTTP | axios | 统一 envelope 解析和超时 |
| 包管理 | npm | `package-lock.json` 入库 |

禁止无确认切换 React/Svelte、引入第二套 UI 库、前端扫描本机 Pi、前端提交 API Key、把整表 CSV 读进浏览器作为主流程。

---

## 3. 信息架构

| 路由 | 名称 | 主要内容 |
|------|------|----------|
| `/screen` | 总览大屏 | AppLayout 内的中央渠道转化桑基图、外围小图、右侧洞察、底部指标条 |
| `/` | 总览 Dashboard | KPI、渠道、转化分布、质量问题、数据概况 |
| `/models` | 模型实验室 | E0–E8、PR/ROC、校准、混淆矩阵、lift、阈值成本 |
| `/customers` | 客户洞察 | 单客预测、SHAP、反事实敏感性分析 |
| `/segments` | 分群画像 | 簇画像、PCA、算法对比、稳定性 |
| `/rules` | 关联规则 | support/confidence/lift 表格与筛选 |
| `/simulate` | 预算模拟 | 期望价值曲线、推荐 K、Top 触达名单 |
| `/agent` | AI 分析台 | 真实 LLM 流式对话、Markdown 消息、运行监控、tool_trace、折叠契约、内联图表 |
| `/pi` | Pi 编排中枢 | PiAgent 配置卡片、健康摘要、skills、审计、一键报告、会话回放 |
| `/about` | 关于与复现 | 启动命令、数据来源、AI 使用边界 |

全局布局：

```text
AppLayout
├─ AppHeader：项目名、健康状态、run_id、runtime
├─ AppSider：五组叙事导航，可折叠
└─ Main：PageHeaderBar + 内容区（max 1440px，padding 24px）
```

`/screen` 只改变内容区构图，不绕开 header/sidebar；≤520px 时侧栏暂隐，主内容占满手机视口，避免总览大屏被折叠菜单挤压。

---

### 3.1 总览大屏主视觉

`/screen` 的主视觉采用“中心大桑基图 + 外圈小图”：

- 中心：`ScreenSankeyOrbit` 使用 ECharts `sankey`，表达“全量样本 → 渠道 → 转化/未转化”的渠道转化分布。
- 外圈：较小图表围绕中心，包括转化环、渠道强度条、横截面阶段条、质量告警、训练/验证/测试划分和默认 run 状态。
- 数据源：`/data/overview`、`/data/dashboard`、`/health`；桑基 link 值只能由后端返回的渠道样本量和转化率计算。
- 口径：`dashboard.caliber` 原样展示；横截面阶段小图不得描述成真实用户逐步流失。
- 响应式：窄屏下中心图与小图改成单列/双列流式排列；≤520px 隐藏侧栏，桑基图切换为纵向紧凑布局，不能相互遮挡或横向溢出。

---

### 3.2 AI 分析台

`/agent` 是运行中的分析驾驶舱，不做营销页。布局固定为：左侧会话列表、中间对话、右侧运行监控；≤900px 单列堆叠，390px 不允许横向滚动。

- Runtime 选择只展示 `pi` 与 `local`；`local` 表示上游 LLM + 宿主工具，不再展示模板模式作为用户入口。
- 左侧会话列表展示标题、runtime、消息数、工具数、更新时间和短会话 ID；列表条目区在组件内部滚动，历史会话增加时不得继续撑高页面。
- 右侧运行监控展示当前阶段（planning/bridge/tooling/replying/done/error）、当前工具、已完成工具数、图表数、SSE 事件数与最近事件时间。
- 消息气泡展示 `runtime`、`llm_model`、`pi_fallback` 与耗时；消息正文使用 Markdown 渲染，至少覆盖标题、列表、引用、链接、行内代码、代码块、表格、分隔线与图片的响应式样式，禁用原始 HTML。
- 五段契约中的观察事实、理解、建议和待确认内容默认折叠；用户主动展开前不得占用完整对话流空间。
- 图表仍由 `render_chart` 的 chart-spec 内联渲染。
- 工具时间线必须实时反映 `tool_start/tool_end/chart/error`，失败工具保留中文错误与重试入口。

---

### 3.3 Pi 编排中枢

`/pi` 作为 PiAgent 运行中枢，页面顺序固定为：

1. 顶部健康摘要：Runtime、Bridge、Skills、Audit 四个轻量指标块。
2. `PiAgentConfigCard`：可保存 runtime、Bridge Model、Base URL、Pi executable、skills/session 目录、Pi timeout、LLM timeout、API Key 写入/清除；Bridge Model 是可搜索、可手填、可从上游刷新的下拉。
3. Runtime 健康：展示默认 runtime、bridge model、Base URL、API Key 掩码、项目内 Pi 路径、SDK 桥接与降级原因。
4. 运行诊断分区：skills 列表、一键分析报告、会话回放、审计日志。

交互约束：

- API Key 输入框为 password；保存成功后清空本地输入，只展示 `api_key_configured` 与 `api_key_preview`。
- “刷新模型”只调用后端 `/agent/pi/models`，由后端访问上游 `/models`；无 Key、上游超时或旧后端未加载时，在字段下方显示中文错误，Bridge Model 仍可手填。
- 非法路径、非法 URL、timeout 越界等错误必须用中文展示在配置卡片内，不弹出密钥明文。
- 页面只调用 `/agent/pi/config`、`/agent/pi/models`、`/agent/pi/status`、`/agent/audit/recent`、`/agent/report`、`/agent/sessions/{session_id}`，不得在浏览器扫描 PATH、探测全局 `pi` 或直接把 Key 发给上游。
- 390px 宽度下配置表单与状态摘要全部单列，输入框和表格不得撑出整页横向滚动。

---

## 4. `/screen` 大屏规范

### 4.1 构图

`/screen` 第一屏必须以中央大图表为主视觉：

- 主体：`ScreenSankeyOrbit` 渲染 ECharts `sankey`，名称为“渠道转化桑基大屏”。
- 中心：桌面桑基主图表达“全量样本 → 渠道 → 转化/未转化”；手机端保持同一数据，但改为纵向紧凑桑基。
- 外圈：至少 6 个小图表或数据微卡，当前实现为转化环、渠道强度、横截面阶段、质量告警、训练划分、默认产物。
- 右侧：洞察栏，承载默认 run、最强渠道、分群、预算、Pi 这类可讲述摘要。
- 底部：指标条，承接口径说明和关键数值。

### 4.2 数据

所有节点和徽章来自以下接口：

`/health`、`/data/dashboard`、`/data/overview`、`/data/cross-matrix`、`/models/metrics`、`/explain/global`、`/segments`、`/rules`、`/simulate/budget`、`/agent/pi/status`。

单接口失败只能降级对应节点、徽章或提示，不允许补假数。`caliber` 字段必须按后端原文展示。

### 4.3 视觉

- 背景：浅色纸面，不使用独立暗色主题。
- 卡片：`--radius-card` 24px；主面板可用 `--radius-panel` 40px。
- 图表：统一浅色轴线与 `--chart-1..8`，不再传入 `screen` 图表主题。
- 图标：按钮和徽章优先使用 `Icon.vue`，不要用文字块假装图标。
- 响应式：窄屏下外圈徽章改为网格流式排列，图表不得和文字重叠。

---

## 5. 接口消费约定

前端只消费 `AGENTS.md` §10 定义的 envelope：

```json
{ "ok": true, "data": {}, "error": null, "request_id": "uuid" }
```

| 场景 | 要求 |
|------|------|
| 预测 | 展示 `proba`、`label`、`threshold`、`run_id`、`model_name` |
| 模型指标 | 主展示 PR-AUC；Accuracy 仅作为对照，不能做主结论 |
| SHAP | 展示 `top_features` 和 `method`，文案使用“模型贡献/敏感性” |
| Agent | 展示 runtime、`llm_model`、`pi_fallback`、运行阶段、Markdown 消息、默认折叠契约和 `tool_trace` |
| ChartCard | 只渲染宿主返回的 chart-spec v1.0，LLM/Pi 不产 spec |
| 大屏 | `caliber` 原样展示；不得把横截面阶段解释为真实漏斗流失率 |
| Pi | `/agent/pi/config` 展示/保存配置；`/agent/pi/models` 获取上游模型候选；`/agent/pi/status` 展示健康；不在前端探测本机路径；不展示 API Key 明文 |

---

## 6. 设计令牌

### 6.1 色彩

| Token | 值 | 用途 |
|-------|----|------|
| `--color-primary-500` | `#5749f4` | 主按钮、激活态、桑基主节点 |
| `--color-secondary-500` | `#14b8a6` | 辅助强调、图表第二色 |
| `--color-gray-50` | `#fafafb` | 弱背景、tile |
| `--color-gray-100` | `#f5f5f5` | 次级背景 |
| `--color-gray-300` | `#c5c5cb` | 默认边框 |
| `--color-gray-500` | `#616167` | 次级文字 |
| `--color-gray-700` | `#403f51` | 正文 |
| `--color-gray-900` | `#2a2933` | 标题 |
| `--bg-page` | `#ffffff` | 页面背景 |
| `--bg-card` | `#ffffff` | 卡片背景 |
| `--bg-tile` | `#f5f5f5` | 徽章、弱容器 |

语义色：success `#22c55e`、warning `#f59e0b`、danger `#ef4444`、info `#0ea5e9`。浅底、边框、文字态见 `tokens.css`。

### 6.2 图表色板

`--chart-1..8` 固定为：

`#5749f4`、`#14b8a6`、`#f59e0b`、`#8b5cf6`、`#ec4899`、`#22c55e`、`#f97316`、`#06b6d4`。

图表实现只从 `frontend/src/utils/chartTheme.ts` 取色。`ChartTheme` 当前只允许 `default`，避免再次分裂出暗色 screen 主题。

### 6.3 字体

| Token | 用途 |
|-------|------|
| `--font-family-base` | 正文、表单、导航 |
| `--font-family-number` | KPI、概率、run_id、表格数值 |
| `--font-family-code` | 代码块、日志、审计片段 |

字号从 `12 / 13 / 14 / 16 / 20 / 24 / 32 / 40px` 取用；不要使用 viewport 字号缩放。

### 6.4 间距与圆角

间距基于 4px 栅格：`4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48px`。

圆角：

| Token | 值 | 用途 |
|-------|----|------|
| `--radius-sm` | 6px | 小标签 |
| `--radius-md` | 12px | 按钮、输入框 |
| `--radius-lg` | 18px | 提示、轻容器 |
| `--radius-card` | 24px | 卡片 |
| `--radius-panel` | 40px | 大屏主面板 |
| `--radius-full` | 999px | 胶囊、状态点 |

### 6.5 阴影和动效

卡片默认用边框 + `--shadow-sm`；悬浮态最多升到 `--shadow-md`。主按钮使用 `--shadow-primary`，但一个区域只保留一个主操作。

动效统一使用 `150ms / 250ms / 400ms` 与 `--motion-easing-default`；`prefers-reduced-motion` 下禁用非必要过渡。

---

## 7. 组件规范

| 组件 | 要求 |
|------|------|
| `Button.vue` | 图标按钮优先，文本按钮只用于明确命令；主按钮数量克制 |
| `KpiCard.vue` | 数字用 `--font-family-number`，趋势只作为辅助 |
| `ChartCard.vue` | 标题、口径、图表、脚注结构固定；未知图型用空态而非崩溃 |
| `PageHeaderBar.vue` | 标题 20px 左右，不要英雄化 |
| `Tag.vue` / `RunIdChip.vue` | 胶囊形，长 run_id 允许截断但 tooltip 保留全量 |
| `MarkdownContent.vue` | 消息 Markdown 渲染层；禁用原始 HTML，长表格和代码块必须组件内横向滚动 |
| `AgentMessage.vue` | 用户/助手区分清楚；消息正文走 Markdown，事实/理解/建议/待确认默认折叠 |
| `ErrorState.vue` / `EmptyState.vue` | 中文说明 + 可执行下一步，不白屏 |

不要卡片套卡片。重复列表项可以是卡片；页面大区块应是无框布局或全宽区域。

---

## 8. 图表规范

1. 所有图表组件必须经 `BaseChart` 创建、销毁和 resize。
2. 图表色、轴线、tooltip 文本色从 `chartTheme.ts` 获取。
3. 长类目优先旋转、滚动或截断，不让文字互相遮挡。
4. PR/ROC、lift、阈值成本、SHAP、PCA 等业务图表必须显示口径或解释限制。
5. 大屏中央主图使用 ECharts `SankeyChart`，外围小图由页面 DOM 与轻量 CSS 图形负责，避免图表和导航逻辑混在一起。

---

## 9. 页面状态

每个页面都要具备：

- 加载态：骨架或轻量 loading。
- 空态：说明需要运行哪个脚本或哪个后端产物缺失。
- 错态：展示中文错误，允许重试。
- 降级态：部分接口失败时尽量保留其他区域。
- 响应式：390px 宽度不出现全页横向溢出；图表内部可滚动。

---

## 10. 工程位置

| 类型 | 位置 |
|------|------|
| 全局 token | `frontend/src/styles/tokens.css` |
| 全局基础样式 | `frontend/src/styles/index.css` |
| 大屏样式 | `frontend/src/styles/screen.css` |
| 图表主题 | `frontend/src/utils/chartTheme.ts` |
| ECharts 注册 | `frontend/src/utils/echarts.ts` |
| 页面 | `frontend/src/views/` |
| 通用组件 | `frontend/src/components/` |
| API client | `frontend/src/api/` |

`frontend/src/style.css` 若保留，只能作为兼容入口，不再承载主要设计系统。

---

## 11. Pencil 约定

`pen/ui.pen` 当前必须至少包含三块顶层画布：

1. `00 · Halo v2 Design Tokens 设计令牌`
2. `01 · Halo v2 Component Library 组件库`
3. `/screen Halo v2 总览大屏`

修改 `.pen` 文件只能用 Pencil MCP 工具，不能用普通文本读取或二进制改写。Pencil 中的 token 名称需要和 `tokens.css` 保持同义，尤其是 primary、gray、chart、radius、screen 兼容 token。

---

## 12. 验收清单

```text
□ /screen 仍在 AppLayout 内，路由 meta 不含 fullscreen
□ 没有 data-theme="screen"、chartColors('screen')、axisTheme('screen')
□ 默认浅色，页面背景不是独立暗色大屏
□ 中央渠道转化桑基图为首屏视觉中心，外围至少 6 个小图或业务微卡
□ 所有业务数字来自 API，接口失败只降级不造假
□ tokens.css、Design Tokens.md、DESIGN.md、ui.pen 同步
□ npm run build 通过
□ 关键页面在桌面和窄屏不发生文字重叠或全页溢出
```
