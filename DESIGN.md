# DESIGN.md — 前端设计系统与 UI 约束

> **地位：** 本仓库**前端（SPA）**的详细设计权威文档。
> **不在本文范围：** 系统架构、数据/ML 协议、FastAPI 路由实现、Agent/Pi 后端逻辑 → 一律见 **`AGENTS.md`**。
> **配套：** 范围见 `docs/plans/`；变更见 `CHANGE.md`；视觉参考库见 **`pen/ui.pen`**（含设计令牌样张、组件库与十路由整页样张）。
> **令牌源：** `docs/plans/Design Tokens.md`（v1.0）——本文 §6 为其前端落地权威解释，两者冲突以本文 §6 为准。
> **版本：** v0.6.0（2026-07-31）— 基于 Design Tokens v1.0 完全重构：浅色·明亮·细腻·现代风格定调；9 类令牌全量收编；十路由样张入库 `pen/ui.pen`。

---

## 0. 文档怎么用

| 你在做什么 | 读哪里 |
|------------|--------|
| 改颜色、字号、间距、圆角、阴影、动效 | **§6 设计令牌**（唯一入口，禁止散值） |
| 改页面、组件、图表、交互文案 | §7–§12 |
| 画新页面 / 改视觉稿 | 先看 `pen/ui.pen` 对应样张，再改代码 |
| 改 API 字段、训练、Agent 工具、Pi 路径 | **AGENTS.md** |
| 前后端字段对不上 | 先改 AGENTS API 节，再改本文 §5「接口消费」 |

**硬规则：**

1. 前端不得发明第二套业务指标口径；所有 AUC/转化率/SHAP 数值必须来自后端响应或后端产物接口。
2. **任何样式值必须可回溯到 §6 令牌**；组件内禁止裸 hex、裸 px 魔法数（§6.11 检查清单）。

---

## 1. 产品前端目标

在浏览器中提供可答辩演示的分析工作台，风格定调：**浅色 · 明亮 · 细腻 · 现代**（数据分析平台质感，非营销落地页）。

1. 一眼看懂数据规模、转化分布与质量告警
2. 对比模型指标（强调 PR-AUC，而非只秀 Accuracy）
3. 对单客户做预测 + SHAP 解释
4. 浏览分群画像与关联规则
5. 与分析 Copilot 对话，**展开 tool_trace** 证明数字有据，会话内联出图
6. 提供复现说明入口（链到命令与数据出处）
7. `/screen` 大屏作为答辩开场全景窗口（唯一暗色作用域，§6.10）

**非目标（前端）：** 营销自动化编排器、复杂权限中心、移动 App、重动画营销落地页、全站暗色模式。

---

## 2. 技术栈锁定

| 项 | 选择 | 说明 |
|----|------|------|
| 框架 | **Vue 3** | Composition API + `<script setup>` 优先 |
| 构建 | **Vite** | 开发端口 **5600**（`vite.config.ts`，可配置） |
| UI 库 | **Element Plus** | 经 §13 CSS 变量覆盖对齐令牌；不引入第二套组件库 |
| 图表 | **ECharts** | 统一经 `BaseChart` 封装 + `chartTheme` 色板 |
| 路由 | Vue Router | history 模式（开发） |
| 状态 | Pinia（按需） | 勿把整表 CSV 塞进 store |
| HTTP | axios | 统一实例与 envelope 解析 |
| 语言 | TypeScript | 类型与 AGENTS DTO 对齐 |
| 包管理 | **npm**（锁定） | `frontend/package-lock.json` 入库 |

**禁止：**

- 无评审切换 React/Svelte
- jQuery、随意 CDN 全局污染
- 在组件内硬编码 `localhost` 且无法用 env 覆盖
- 为"好看"引入大型 3D/粒子库（答辩无必要）
- 站点级玻璃拟态、满屏 aurora 渐变背景（与"数据产品感"冲突）

---

## 3. 设计原则

| 原则 | 落地要求 |
|------|----------|
| 数据产品感 | 干净、克制、偏仪表盘；少插画少装饰线；卡片以 `shadow-sm` 或纯边框表达层级 |
| 信息优先 | 数字与表格对比优先于营销风大图；KPI 数字用数字字体（§6.2） |
| 层级靠令牌 | 背景三级分层 `bg-page → bg-card → bg-subtle`；阴影克制使用（§6.5） |
| 一致性 | 同一语义同一颜色/字号/间距；状态色不跨语义借用 |
| 可投影 | 正文对背景对比度 ≥ 4.5:1（`text-body #334155` on `#FFFFFF` ≈ 9.9:1）；避免 `gray-400` 承载关键信息 |
| 色盲友好 | 不只靠红绿；SHAP 双向用蓝/红两端色 + 0 轴 + 文字图例；涨跌辅以箭头图标 |
| 动效有度 | 一切动效来自 §6.7 动效令牌；`prefers-reduced-motion` 全部关闭 |

---

## 4. 信息架构与路由

### 4.1 站点地图（十路由）

| 路由 | 名称 | 层级 | 主要内容 |
|------|------|------|----------|
| `/screen` | 总览大屏 | 开场 | 全屏暗色作用域（`meta.fullscreen` 绕过 AppLayout）：KPI 磁贴、伪漏斗、渠道/交叉/分布图、E0–E8 mini 榜、SHAP Top8 |
| `/` | 总览 Dashboard | 描述性分析 | KPI、转化分布、渠道表现、质量告警、数据摘要 |
| `/models` | 模型实验室 | 预测建模 | E0–E8 对比表（CV/CI/Brier）、PR/ROC、校准、混淆矩阵、lift、阈值-成本 |
| `/customers` | 客户洞察 | 预测建模 | 查 ID/表单特征 → 概率、标签、SHAP、反事实（模型行为口径，折叠区） |
| `/segments` | 分群画像 | 深度挖掘 | 簇列表、自动画像名、PCA 投影、多算法对比、稳定性徽章 |
| `/rules` | 关联规则 | 深度挖掘 | 规则表、Lift 筛选、免责声明 |
| `/simulate` | 预算模拟 | 深度挖掘 | 参数表单、期望收益曲线、推荐 K、Top 名单、CSV 导出 |
| `/agent` | AI 分析台 | AI 与系统 | 对话、runtime 徽章、五段契约、tool_trace、**内联 ChartCard** |
| `/pi` | Pi 编排中枢 | AI 与系统 | runtime 状态、skills 列表、一键报告、审计表格、会话回放 |
| `/about` | 关于与复现 | AI 与系统 | 启动命令、数据出处、AI 使用说明、链接 AGENTS |

后端产物缺失时：导航可显示但内容为 EmptyState「请先运行 scripts」，**不要**死链 404 吓退演示。

### 4.2 全局布局

```text
┌─────────────────────────────────────────────────────────────┐
│ AppHeader（h=64px）：项目名 | 健康状态点 | run_id | Runtime 徽章 │
├──────────────┬──────────────────────────────────────────────┤
│ AppSider     │  PageHeaderBar（标题 20px + 说明 + 主操作）     │
│ 240↔64px     │  ─────────────────────────────────────────   │
│ 五组叙事：    │  Content（max 1440px 居中，padding 24px）      │
│ ▸ 总览大屏    │  卡片 / 分栏 / 表图                            │
│ ▸ 描述性分析  │                                               │
│ ▸ 预测建模    │                                               │
│ ▸ 深度挖掘    │                                               │
│ ▸ AI 与系统   │                                               │
│ [折叠按钮]    │                                               │
└──────────────┴──────────────────────────────────────────────┘
```

- **桌面优先**（答辩投影 1366×768 及以上完整可用；设计基准 1280–1440，大屏样张 1920）
- **侧栏：** 展开 `--layout-sidebar-width`（240px），折叠 `--layout-sidebar-collapsed`（64px）；五组叙事分组显式呈现"数据分析→数据挖掘"由浅入深；折叠态仅图标（均带 `title` 无障碍）；`width` transition 用 `motion-duration-base`（`< 992px` 自动收为图标栏）
- **路由切换：** 轻 fade（`motion-duration-fast`，out-in），`prefers-reduced-motion` 关
- 图表允许横向滚动，不挤碎轴标签

### 4.3 用户关键路径（演示）

0. **（开场）`/screen` 大屏全景**：规模 → 伪漏斗 → 渠道/交叉/分布 → E0–E8 矩阵 → SHAP，一页讲完由浅入深
1. `/` 总览确认数据与质量 →
2. `/models` 指出 PR-AUC 与 Dummy 陷阱、E7 Stacking 主线 →
3. `/customers` 解释 1 个高概率样例（反事实手动展开）→
4. `/agent` 问「画各渠道转化率柱状图」→ Pi 编排 + 内联图表 + 展开 trace →
5. `/segments` `/rules` `/simulate` 快速带过

前端须保证上述路径**点击次数少、无阻塞弹窗连环**。

---

## 5. 接口消费约定（前端视角）

> 路径与字段权威在 **AGENTS.md §10**；本节只约束前端如何用。

### 5.1 HTTP 基础

- `baseURL`：`import.meta.env.VITE_API_BASE_URL` 或默认 `http://127.0.0.1:9800/api/v1`
- 超时：普通 30s；`/agent/chat` 建议 120s
- 统一解析 envelope：`ok === true` 用 `data`；否则抛出 `error.message`（中文展示）
- 每个列表/详情请求失败：页面内 `ErrorState`，而不是白屏

### 5.2 前端必须遵守的字段

| 场景 | 必须展示/携带 |
|------|----------------|
| 预测结果 | `proba`（4 位小数）、`label`、`threshold`、`run_id` |
| 模型表 | PR-AUC、ROC-AUC；Accuracy 若展示须标注「仅对照」 |
| SHAP | `top_features` 列表；标明 `method` |
| Agent | 可见 `tool_trace`；runtime 名称；session 可续聊 |
| 大屏口径 | `caliber` 字段**原样渲染**（横截面/非 cohort/无时序声明） |
| Pi 状态 | 仅展示后端 `/agent/pi/status` 结果（含 `bridge_ready`）；前端不扫描用户磁盘找 `pi` |

### 5.3 前端禁止

- 禁止本地用假随机数生成「演示 AUC」
- 禁止把 API Key 写进前端 env 提交库（LLM Key 只在后端）
- 禁止前端直接读 `data/*.csv` 当生产路径

---

## 6. 设计令牌（Design Tokens）— 唯一视觉真相

> 风格定位：**浅色 · 明亮 · 细腻 · 现代**。全部令牌实现于 `frontend/src/styles/tokens.css`，业务代码**优先使用语义化别名**（`--bg-*` / `--text-*` / `--border-*`），基础色阶仅供令牌层与图表层引用。

### 6.1 色彩令牌（Color）

**品牌主色（清澈明亮的蓝，传递专业、可信、数据感）：**

| 令牌 | 色值 | 用途 |
|---|---|---|
| `--color-primary-50` | `#EFF6FF` | 浅底悬浮、选中背景（侧栏 active 底、chip） |
| `--color-primary-100` | `#DBEAFE` | 弱强调背景、标签底色 |
| `--color-primary-200` | `#BFDBFE` | 禁用态、分割强调 |
| `--color-primary-300` | `#93C5FD` | 辅助图形、次级图标、输入框 hover 边框 |
| `--color-primary-400` | `#60A5FA` | 悬浮态（hover） |
| `--color-primary-500` | `#3B82F6` | **主色基准**：主按钮、链接、激活态、输入框 focus 边框 |
| `--color-primary-600` | `#2563EB` | 按压态（active）、深色强调 |
| `--color-primary-700` | `#1D4ED8` | 深色文字强调 |

**辅助色（青色系，次要操作与信息补充）：**

| 令牌 | 色值 | 用途 |
|---|---|---|
| `--color-secondary-50` | `#F0FDFA` | 浅底背景 |
| `--color-secondary-100` | `#CCFBF1` | 弱强调背景 |
| `--color-secondary-400` | `#2DD4BF` | 悬浮态 |
| `--color-secondary-500` | `#14B8A6` | 辅助色基准（图表第 2 色同值） |
| `--color-secondary-600` | `#0D9488` | 按压态 |

**语义色：**

| 令牌 | 色值 | 浅色底（`*-bg`） | 用途 |
|---|---|---|---|
| `--color-success` | `#22C55E` | `#F0FDF4` | 成功、正向指标、健康点 |
| `--color-warning` | `#F59E0B` | `#FFFBEB` | 质量告警、待处理、disclaimer 底 |
| `--color-danger` | `#EF4444` | `#FEF2F2` | 错误、SHAP 负贡献、下降 |
| `--color-info` | `#0EA5E9` | `#F0F9FF` | 信息提示、中性通知 |

**中性色（偏冷灰，干净通透）：**

| 令牌 | 色值 | 用途 |
|---|---|---|
| `--color-gray-0` / `--color-white` | `#FFFFFF` | 卡片、弹窗底色 |
| `--color-gray-50` | `#F8FAFC` | **页面主背景** |
| `--color-gray-100` | `#F1F5F9` | 次级背景、表头、骨架屏 |
| `--color-gray-200` | `#E2E8F0` | 分割线、边框、图表网格线 |
| `--color-gray-300` | `#CBD5E1` | 禁用边框、占位图标 |
| `--color-gray-400` | `#94A3B8` | 占位文字、辅助图标 |
| `--color-gray-500` | `#64748B` | 次级文字、坐标轴文字 |
| `--color-gray-700` | `#334155` | **正文文字** |
| `--color-gray-900` | `#0F172A` | **标题文字**、强强调 |

**语义化别名（业务代码首选）：**

| 别名 | 解析 |
|---|---|
| `--bg-page` | `var(--color-gray-50)` |
| `--bg-card` | `var(--color-white)` |
| `--bg-subtle` | `var(--color-gray-100)` |
| `--text-title` | `var(--color-gray-900)` |
| `--text-body` | `var(--color-gray-700)` |
| `--text-secondary` | `var(--color-gray-500)` |
| `--text-placeholder` | `var(--color-gray-400)` |
| `--border-default` | `var(--color-gray-200)` |
| `--border-hover` | `var(--color-primary-300)` |
| `--border-focus` | `var(--color-primary-500)` |

**数据可视化色板（8 色循环，按序取用）：**

| 序号 | 令牌 | 色值 | 序号 | 令牌 | 色值 |
|---|---|---|---|---|---|
| 1 | `--chart-1` | `#3B82F6` 蓝 | 5 | `--chart-5` | `#EC4899` 粉 |
| 2 | `--chart-2` | `#14B8A6` 青 | 6 | `--chart-6` | `#22C55E` 绿 |
| 3 | `--chart-3` | `#F59E0B` 橙 | 7 | `--chart-7` | `#F97316` 橘红 |
| 4 | `--chart-4` | `#8B5CF6` 紫 | 8 | `--chart-8` | `#06B6D4` 湖蓝 |

- 图表网格线：`--chart-grid` = `gray-200`；坐标轴文字：`--chart-axis-text` = `gray-500`
- SHAP 双向专用：正贡献 `--chart-1`（蓝）/ 负贡献 `--color-danger`（红），中间 0 轴 + 图例写清「推向转化 / 拉低转化」
- 单图类目超过 8 个时合并为「其他」；禁止每页临时选色

### 6.2 字体令牌（Typography）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--font-family-base` | `"Inter", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif` | 界面正文 |
| `--font-family-number` | `"DIN Alternate", "Roboto Mono", "SF Mono", monospace` | **数字、指标、表格数值**（等宽防跳动） |
| `--font-family-code` | `"JetBrains Mono", "Fira Code", Consolas, monospace` | 代码块、JSON、命令 |

**字号 / 行高阶梯：**

| 令牌 | 字号/行高 | 用途 |
|---|---|---|
| `--font-size-xs` | 12 / 20 | 辅助说明、标签、表格次级信息、disclaimer |
| `--font-size-sm` | 13 / 22 | 表格正文、表单 |
| `--font-size-md` | 14 / 24 | **正文基准**、按钮 |
| `--font-size-lg` | 16 / 26 | 卡片标题、强调正文 |
| `--font-size-xl` | 20 / 30 | 页面标题（PageHeaderBar） |
| `--font-size-2xl` | 24 / 34 | 大屏模块标题 |
| `--font-size-3xl` | 32 / 42 | 核心指标数字（KPI 卡） |
| `--font-size-4xl` | 40 / 52 | 大屏主指标 |

**字重：** `--font-weight-regular` 400（正文）/ `-medium` 500（表头、强调正文）/ `-semibold` 600（卡片/模块标题、指标数字）/ `-bold` 700（页面主标题、大屏标题）。

行高 1.5–1.6 区间，不要密不透风；数字一律 `tabular-nums`（`.tabular-nums` 工具类）。

### 6.3 间距令牌（Spacing，4px 栅格）

| 令牌 | 值 | 典型用途 |
|---|---|---|
| `--space-1` | 4px | 图标与文字间距 |
| `--space-2` | 8px | 紧凑元素内边距 |
| `--space-3` | 12px | 表单项间距 |
| `--space-4` | 16px | **基准间距**：卡片内边距 |
| `--space-5` | 20px | 卡片标题与内容间距 |
| `--space-6` | 24px | 卡片之间、模块间距、页面左右留白 |
| `--space-8` | 32px | 大区块间距 |
| `--space-10` | 40px | 页面区块间距 |
| `--space-12` | 48px | 页面顶部留白 |

### 6.4 圆角令牌（Radius）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--radius-sm` | 4px | 标签、小徽章 |
| `--radius-md` | 6px | 按钮、输入框 |
| `--radius-lg` | 8px | **卡片基准** |
| `--radius-xl` | 12px | 弹窗、大型面板 |
| `--radius-full` | 9999px | 胶囊按钮、状态点、chip |

禁止全站统一大圆角；弹窗 `radius-xl`、卡片 `radius-lg`、控件 `radius-md`，层次分明。

### 6.5 阴影令牌（Shadow，低透明偏蓝，避免脏感）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--shadow-xs` | `0 1px 2px 0 rgba(15,23,42,.04)` | 输入框、小控件 |
| `--shadow-sm` | `0 1px 3px 0 rgba(15,23,42,.06), 0 1px 2px -1px rgba(15,23,42,.04)` | **卡片基准** |
| `--shadow-md` | `0 4px 12px -2px rgba(15,23,42,.08), 0 2px 4px -2px rgba(15,23,42,.04)` | 悬浮卡片、下拉菜单 |
| `--shadow-lg` | `0 12px 32px -8px rgba(15,23,42,.12), 0 4px 8px -4px rgba(15,23,42,.06)` | 弹窗、抽屉 |
| `--shadow-primary` | `0 4px 12px -2px rgba(59,130,246,.32)` | 主按钮悬浮态 |

**规则：** 常规卡片 `shadow-sm` 或纯边框二选一（表格卡倾向纯边框）；hover 升一级；禁止多重阴影堆叠。

### 6.6 边框令牌（Border）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--border-width-default` | 1px | 常规边框 |
| `--border-color-default` | `#E2E8F0` | 卡片、表格、输入框 |
| `--border-color-hover` | `#93C5FD` | 输入框悬浮 |
| `--border-color-focus` | `#3B82F6` | 输入框聚焦（外圈 2px `primary-100` 光晕可选） |

### 6.7 动效令牌（Motion）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--motion-duration-fast` | 150ms | hover 变色、图标反馈、路由 fade |
| `--motion-duration-base` | 250ms | **基准**：侧栏折叠、展开收起、状态切换 |
| `--motion-duration-slow` | 400ms | 弹窗、抽屉、页面转场、大屏板块入场 |
| `--motion-easing-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | 通用缓动 |
| `--motion-easing-out` | `cubic-bezier(0, 0, 0.2, 1)` | 进入动画 |
| `--motion-easing-in` | `cubic-bezier(0.4, 0, 1, 1)` | 退出动画 |

`prefers-reduced-motion: reduce` 时全部降为 0ms。

### 6.8 层级令牌（Z-Index）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--z-sticky` | 100 | 吸顶表头、吸顶导航 |
| `--z-dropdown` | 1000 | 下拉菜单 |
| `--z-overlay` | 1300 | 遮罩层 |
| `--z-modal` | 1400 | 弹窗 |
| `--z-toast` | 1600 | 全局消息提示 |
| `--z-tooltip` | 1700 | 气泡提示 |

### 6.9 布局令牌（Layout）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--layout-sidebar-width` | 240px | 侧边栏展开宽度 |
| `--layout-sidebar-collapsed` | 64px | 侧边栏收起宽度 |
| `--layout-header-height` | 64px | 顶部导航高度 |
| `--layout-content-max` | 1440px | 内容区最大宽度（居中） |
| `--layout-page-padding` | 24px | 页面内容左右留白 |
| `--chart-height` | 280px | 图表默认高度 |
| `--chart-height-lg` | 320px | 信息密集图（阈值扫描/PCA/预算曲线） |

**断点：** `sm` 640 / `md` 768 / `lg` 1024 / **`xl` 1280（设计基准）** / `2xl` 1920（大屏）。

### 6.10 大屏作用域令牌（`[data-theme='screen']`，唯一暗色例外）

`/screen` 为 `data-theme="screen"` **作用域暗色**（`styles/screen.css`，变量仅子树生效，不扩散全站；全站暗色仍是 P2 不做）。

| 令牌 | 值 | 用途 |
|---|---|---|
| `--screen-bg-0` | `#081428` | 页面基底（叠径向渐变提亮） |
| `--screen-bg-1` | `#0C1F3D` | 板块底 |
| `--screen-bg-2` | `#12294E` | 板块内嵌层、表头 |
| `--screen-border` | `rgba(96,165,250,.18)` | 板块描边（1px 发光感） |
| `--screen-text` | `#DBE9FF` | 正文 |
| `--screen-text-secondary` | `#8FB3E6` | 次要、轴标签 |
| `--screen-chart-1..8` | 高饱和 8 色 | 大屏图表序列色（`chartColors('screen')` 运行时读取） |

- 大屏数字字体：`'Rajdhani', 'Orbitron', var(--font-family-number)`（CDN 加载 + `font-display: swap`，**离线答辩回落系统字体**，仅观感变化）
- 板块入场 `rise` 动画 300–400ms（`--motion-duration-slow` + easing-out），`prefers-reduced-motion` 关
- 禁止 3D/粒子库（§2）

### 6.11 令牌检查清单（PR 自查）

```text
□ 组件内 grep 不到裸 hex（图表经 chartTheme，其余经 CSS 变量）
□ 间距只出现 4/8/12/16/20/24/32/40/48
□ 圆角只出现 4/6/8/12/9999
□ 过渡时长只出现 150/250/400ms 三档
□ 新颜色先回 §6.1 找令牌，找不到先补令牌再用
□ Element Plus 覆盖样式经 :root CSS 变量，不逐组件穿透
```

---

## 7. 组件规范

### 7.1 基础组件（优先 Element Plus，经令牌覆盖）

| 用途 | 组件 | 令牌要点 |
|------|------|----------|
| 按钮 | `el-button` | primary = `primary-500`，hover `primary-400` + `shadow-primary`，active `primary-600`；圆角 `radius-md` |
| 表单 | `el-form` + rules | 边框三态 default/hover/focus（§6.6）；提交防抖 |
| 表格 | `el-table` | 表头 `gray-100` 底、`font-weight-medium`；数值列 `font-family-number`；空数据 `slot empty` |
| 标签 | `el-tag` | 语义色浅底 + 深字（如 success = `#F0FDF4` 底 + `#15803D` 字） |
| 提示 | `el-alert` / `ElMessage` / `ElMessageBox` | 四种语义色，图标 + 浅底 |
| 加载 | `v-loading` | 骨架屏用 `gray-100` → `gray-200` shimmer |
| 抽屉/对话框 | dialog `radius-xl` + `shadow-lg`；drawer 同 | 遮罩 `z-overlay` |

### 7.2 业务组件（自建，视觉参考 `pen/ui.pen` 同名样张）

| 组件 | 职责 | 关键规格 |
|------|------|----------|
| `BaseChart` | ECharts 生命周期封装（init/ResizeObserver/dispose/watch） | props: `option/height/theme`；唯一图表出口（§8.0） |
| `ChartCard` | chart-spec v1.0 → option 映射渲染 + caliber/disclaimer 脚注 | 供 `/agent` 内联；未知 chart_type EmptyState 兜底 |
| `KpiCard` | 标题、主数值（`3xl` + 数字字体 + `semibold`）、副文案、来源 hint | 数字**不跳动**：加载用骨架，不用 0 起跳动画 |
| `PageHeaderBar` | 标题 `xl/600`、描述 `sm/text-secondary`、右侧 actions | 与内容间距 `space-6` |
| `ModelMetricsTable` | 多 run 指标；PR-AUC 列高亮（`primary-50` 底 + `semibold`） | Dummy 行 tag；E4/E6 行弱化（opacity .65 + 「展示降权」tag） |
| `ShapBarChart` | 水平条形；正负双向（蓝/红 + 0 轴） | 图例「推向转化 / 拉低转化」 |
| `QualityIssueList` | 质量问题计数与说明 | warning 浅底条目 |
| `DisclaimerBanner` | 相关非因果固定文案（§11.2） | warning 浅底 + `radius-lg` |
| `AgentMessageList` | 气泡列表 | 用户右对齐 `primary-500` 底白字；助手左对齐白卡 |
| `ToolTracePanel` | 工具名、参数摘要、成功/失败、耗时（折叠面板） | 代码字体展示参数 |
| `RuntimeBadge` | pi / local / template + stub/降级原因 tooltip | pi = 胶囊 + 健康点 |
| `RocPrCurveChart` | PR / ROC 双联曲线（随机基线虚线） | run 下拉联动 |
| `CalibrationChart` | 完美对角线 + before/after 双色 | |
| `ConfusionHeatmap` | 2×2 混淆矩阵热力（x=预测 y=实际） | |
| `LiftChart` | 十分位 capture_rate 柱 + lift 折线（右轴） | 右轴须标注 |
| `ThresholdScanChart` | P/R/F1 三线 + 期望成本右轴 + 三档 markLine | 当前/成本最优/选中 |
| `ScatterPcaChart` | PCA 2D 散点（按簇着色 + 自动画像名图例） | `chart-height-lg` |
| `BudgetCurveChart` | 净收益主线 + 毛收益/转化数虚线 + 推荐 K markLine | `chart-height-lg` |
| `CounterfactualCurveChart` | 单特征扰动 proba 曲线 + 当前样本点 + 目标线 | 模型行为口径标注 |
| `EmptyState` | 无数据时引导运行后端脚本 | 图标 + 命令代码块 |
| `ErrorState` | 展示后端 `error.message` + 重试按钮 | |

### 7.3 KPI 卡规则

- 主数字最大最重（`3xl` + `font-family-number` + `semibold`）
- 副标题说明指标含义（如「测试集 PR-AUC」）
- 若有对比，写清对比对象（vs Dummy）
- 加载时用骨架屏，避免数字从 0 跳动误导

### 7.4 表格规则

- 概率/AUC：**4 位小数**；转化率：百分比 **2 位**（如 87.65%）；大整数：千分位
- 数值列 `font-family-number` + `tabular-nums` + 右对齐
- 长 ID：可复制按钮；默认不关边框到「看不清行」

### 7.5 表单规则

- 标签中文；placeholder 给示例而非复述标签
- 数字输入限制范围（后端 meta 优先）
- 主按钮「预测 / 发送」在表单可视区内；提交中 disable 防连点

---

## 8. 图表规范（ECharts）

### 8.1 封装与主题

- **唯一出口：** 所有图表经 `components/BaseChart.vue`（init / ResizeObserver 监听容器 / dispose / watch option 集中承接）；业务图表组件只产出 `computed option` 后 `<BaseChart :option="option" />`，禁止组件内自写 init/resize 样板与 `echarts.use`
- **按需注册集中点：** `utils/echarts.ts`（Bar/Line/Scatter/Heatmap/Funnel + Grid/Legend/MarkLine/Title/Tooltip/VisualMap + CanvasRenderer）
- **色板单一真相：** `utils/chartTheme.ts` 与 §6.1 色板逐值对齐；`chartColors(theme)` / `axisTheme(theme)` 支持 default 与 screen 两套作用域（大屏读 `--screen-chart-1..8`），组件内禁止裸 hex
- **高度：** 默认 `--chart-height`（280px）；信息密集图传 `height="var(--chart-height-lg)"`（320px）

### 8.2 通用

- 每图必有：标题（或卡片标题）、图例（多系列）、轴名称（若适用）
- tooltip 中文；数值格式与表格一致（§7.4）
- 网格线 `--chart-grid`、轴文字 `--chart-axis-text`
- 动画默认轻量；`prefers-reduced-motion` 关
- 容器须设明确高度，禁止高度 0

### 8.3 推荐图表类型

| 页面 | 图表 | 备注 |
|------|------|------|
| 总览 | 转化 0/1 占比环图；渠道柱状 | 环图类别 ≤5；多类改条形 |
| 模型 | PR/ROC 双联；校准；混淆热力；lift 柱+折线；阈值-成本多线 | run 下拉联动；阈值滑块联动 |
| 客户 | SHAP 水平条；反事实单特征曲线 | 按绝对值排序可切换 |
| 分群 | PCA 2D 散点；簇大小柱状；多算法对比表 | 雷达维数 ≤8 |
| 规则 | 一般用表；Lift 可用条形 | 避免强行 3D |
| 模拟 | 期望收益曲线（净/毛/转化数） | 推荐 K markLine |

**spec 驱动渲染路径：** 后端 `render_chart` 工具返回 chart-spec v1.0（字段见 AGENTS §10.3），前端 `ChartCard` 按 `chart_type` 映射为 option（色板仍走 `chartColors()`）；`caliber`/`disclaimer` 必须渲染为卡片脚注。新增 chart_type 须同步改 ChartCard 与本节。

### 8.4 禁止

- 无意义 3D 饼图
- 双 Y 轴故意夸大差异却不说明
- 堆叠面积图信息过载却无筛选
- 伪漏斗用漏斗形（阶段为横截面独立计数、非嵌套，漏斗形误导出流失率 → 用柱状）

---

## 9. 布局与栅格

- 使用 Element `el-row`/`el-col` 或 CSS grid；内容区 `max-width: var(--layout-content-max)` 居中
- Dashboard：顶排 3–4 个 KPI 卡（`card-grid` auto-fill），下方 2 列「分布图 | 质量列表」
- 模型页：上表下图或左表右说明
- 客户页：左表单右结果（宽屏）；窄屏上下堆叠
- AI 台：左对话主栏（≈62%）+ 右上下文/trace（≈38%）；窄屏 trace 改折叠面板
- 大屏：CSS Grid 12 列，gap 14，边距 24（§12.10）

**密度：** 默认舒适密度；表格可「中等」；不要默认用 Element 的 mini 导致投影看不清。

---

## 10. 文案、语气与免责声明

### 10.1 语气

- 专业、简洁、本科答辩友好；少用「赋能」「打造闭环」等空话
- 错误提示说明「现象 + 可尝试动作」（如：模型未加载，请先运行 `python scripts/run_all.py`）

### 10.2 固定免责声明（须在分群、规则、Agent、策略建议、大屏页脚可见）

> 以下洞察基于历史数据中的**相关关系**与模型估计，**不构成因果证明**，也不构成实际投放收益承诺。

### 10.3 指标命名展示

| 内部字段 | UI 展示名 |
|----------|-----------|
| pr_auc | PR-AUC |
| roc_auc | ROC-AUC |
| f1 | F1 |
| accuracy | Accuracy（仅对照） |
| proba | 转化概率 |

---

## 11. 交互与反馈

| 场景 | 行为 | 动效 |
|------|------|------|
| hover | 按钮/卡片/行状态变化 | `fast` + easing-default |
| 加载 > 300ms | 显示 loading / 骨架 | shimmer |
| 成功轻操作 | Message 成功（自动关闭） | `base` |
| 展开收起（反事实折叠、侧栏） | 高度/宽度过渡 | `base` |
| 弹窗/抽屉 | 遮罩 + 面板进入 | `slow` + easing-out |
| 路由切换 | 轻 fade（out-in） | `fast` |
| 大屏板块入场 | rise（translateY 8px→0 + opacity） | `slow`，仅首屏一次 |
| 表单校验失败 | 定位到首个错误字段 | — |
| 会话丢失 | Agent 可新开 session，提示旧会话不可用 | — |

**原则：** 反馈即时可感知但不抢戏；不做复杂全局快捷键（P0）；避免长动画耽误演示。

---

## 12. 页面级详细约束

### 12.1 总览 `/`

**必须有：** 样本量、正/负样本数或转化率；质量问题条数入口（可点到说明）；至少 1 个分布图（渠道或转化）；后端未就绪时 EmptyState。
**不要：** 无数据时假装已有漂亮假图。

### 12.2 模型实验室 `/models`

**必须有：**

- E0–E8 对比表，**PR-AUC 列优先高亮**；Dummy 行 tag；**E4/E6 消融行弱化（opacity .65 + 「展示降权」tag，代码/端点不删）；E5/E7/E8 主线保留高亮**
- 列：PR-AUC、CV 5-fold 均值±std、95% CI（bootstrap）、ROC-AUC、F1、Brier、Accuracy（仅对照）、阈值
- run 下拉联动：PR/ROC 双联曲线、混淆矩阵热力、lift 图
- 阈值-成本分析：多线图 + 滑块联动（当前/成本最优/选中三档 markLine）
- 校准曲线（E8）：完美对角线 + before/after 双色
- 全局 SHAP 条形
- 顶部口径文案：CI 重叠不宣称更优；消融不参选默认

### 12.3 客户洞察 `/customers`

**必须有：**

- 输入：CustomerID **或** 特征表单（二选一主路径）；「样例填充」按钮（答辩用）
- 输出：概率、标签、阈值、run_id
- SHAP Top 特征图或表
- **反事实面板：ElCollapse 默认收起**，标题「反事实分析 · 模型行为分析（敏感性），非因果，不构成投放建议」；展开后：扰动特征下拉 + 目标 proba → 单特征曲线 + 达标步骤表 + 强制 disclaimer
- 批量预测（上限 200）

### 12.4 分群 `/segments`

- 簇表：ID、**自动画像名**、占比、事后转化率、3–5 个显著特征
- **稳定性徽章：** bootstrap ARI 均值±std（≥0.75 绿 / ≥0.5 蓝 / 否则黄）
- PCA 2D 散点（按簇着色，图例带自动画像名）
- 多算法对比表（KMeans/GMM/Agglomerative × K；silhouette/CH/BIC；主分群行高亮）——**主线内容，保持正常视觉权重**
- 策略文案区必须带免责声明；无产物 EmptyState

### 12.5 规则 `/rules`

- 表列：前件、后件、support、confidence、lift；可按 lift 排序/筛选；顶部免责声明

### 12.6 AI 分析台 `/agent`

**必须有：**

- 多轮消息列表 + 发送框 + 加载中状态
- **Runtime 展示与切换**（默认 pi；切换调后端，失败提示；stub/降级显示原因）
- 每条助手消息可展开 **tool_trace**（ToolTracePanel）
- **内联图表：** `tool_trace` 中 `render_chart` 成功条目在 ToolTracePanel 上方渲染 `ChartCard`（spec 驱动，数字来自宿主工具非 LLM）
- **五段契约完整渲染：** observed_facts / inferences / recommendations / open_questions / tool_trace
- `pi_fallback=true` 时显示「Pi 降级」警告 tag
- 建议「示例问题」chips（含画图指令例）降低冷启动

**交互细节：** Enter 发送、Shift+Enter 换行；失败消息可「重试」；不渲染未消毒 HTML。

### 12.7 预算模拟 `/simulate`

- 参数表单：单客转化价值、单次触达成本、预算上限（可空）+ 盈亏平衡 proba 回显
- KPI 行：推荐 K、期望净收益、期望转化数、评估人群（test n + run_id）
- 期望收益曲线（BudgetCurveChart）+ Top 名单预览表（≤50）+「导出名单 CSV」（显示落盘路径）
- 固定 disclaimer：期望值口径，非因果收益承诺

### 12.8 Pi 编排中枢 `/pi`

- Runtime 状态卡：默认 runtime、桥接三要素（`bridge_ready` + note）、stub/真实安装 tag、降级原因、会话数
- Skills 列表（名称 + 描述，来自 `/agent/pi/status`.skills_detail）
- 一键报告：标题输入 + 生成 → n_sections_ok/n_sections、落盘路径、digest 预览、tool_trace
- 审计表格（最近 N 条：时间/runtime/用户消息/工具/会话/耗时）
- 会话回放：输入 session_id → 展示完整会话 JSON
- 口径文案：Pi 仅 `tools/pi-cli/`，禁止全局回退

### 12.9 关于 `/about`

- 复现命令（与 AGENTS 一致）；数据来源链接/说明
- 文档入口：`AGENTS.md` / 本文件 / 计划书路径说明；AI 使用说明摘要（毕设诚信）

### 12.10 总览大屏 `/screen`

**栅格（CSS Grid 12 列，gap 14，边距 24；1366 档媒体查询收缩）：**

| 行 | 板块（列跨） | 数据源 |
|---|---|---|
| Header | 标题 + 「横截面口径·无时序」徽章 ‖ 健康点 + run_id + 返回工作台 | `/health` |
| R1 | 6× KPI 磁贴（样本量/正类占比/总支出/均CTR/访问深度/复购占比） | `/data/dashboard`.kpis |
| R2 | 行为伪漏斗柱状(4) ‖ 渠道转化率(4) ‖ 渠道×类型热力(4) | dashboard.funnel / `/data/overview` / `/data/cross-matrix` |
| R3 | 年龄/收入/AdSpend 直方图 各(4) | dashboard.histograms |
| R4 | E0–E8 mini 表(7，PR-AUC 主列 + Dummy/消融/默认 tag) ‖ SHAP Top8(5) | `/models/metrics` / `/explain/global` |
| Footer | caliber 原文 + 相关非因果免责声明 | DTO 字段 |

**约束：** 伪漏斗用**柱状图**（§8.4）；每个板块独立请求、独立降级（失败仅该板块提示），全站不造假数；口径文案来自后端 `caliber` 原样渲染；入场动画 `slow` + reduced-motion 关。

---

## 13. 前端工程结构

```text
frontend/
  index.html
  package.json
  vite.config.ts
  .env.example                 # VITE_API_BASE_URL=
  src/
    main.ts
    App.vue                    # meta.fullscreen 分支：/screen 绕过 AppLayout
    styles/
      tokens.css               # §6 令牌实现（含 Element Plus 变量覆盖）
      screen.css               # §6.10 大屏作用域
      index.css
    router/index.ts
    api/                       # axios 实例与各模块 API
    components/                # BaseChart / ChartCard / 业务组件
    views/                     # 十路由页面级
    utils/                     # echarts.ts / chartTheme.ts / format*
    layouts/AppLayout.vue      # 五组叙事侧栏 + 折叠
```

**约定：** `views` 不写复杂请求细节，放 `api/`；格式化函数集中（`formatPercent`、`formatAuc`）；`components` 不依赖 `views`（禁止循环依赖）。

---

## 14. 状态管理

| Store | 内容 |
|-------|------|
| `app` | health、版本、runtime、侧栏折叠（本地 ref 亦可，CHANGE 已注明不引 Pinia 的理由） |
| `metrics` | 缓存的模型对比；注意失效刷新 |
| `agent` | session_id、messages、pending、最后 error |

**原则：** 服务器为真相来源；刷新页面后可重新拉取。

---

## 15. 性能

- 路由级懒加载页面
- ECharts 按需引入统一在 `utils/echarts.ts`；图表经 `BaseChart`（ResizeObserver 监听容器，侧栏折叠/窗口缩放自动 resize，unmount 即 dispose）
- 大表分页（规则列表）
- CDN 字体仅大屏用，`font-display: swap`；提交前注意包体体积不必过度优化

---

## 16. 安全（前端侧）

- 不存储 API Key；不使用 `v-html` 渲染 Agent 原始输出（除非消毒）
- 外链 `rel="noopener"`；环境变量仅 `VITE_*` 非机密配置

---

## 17. 无障碍

- 对比度：正文与背景 ≥ 4.5:1；焦点可见（键盘可点主按钮）
- 图表不只依赖颜色传达唯一信息；图标按钮补充文案或 `aria-label`
- **语言：仅简体中文**（P0 不做 i18n 框架）

---

## 18. 空态 / 错态 / 加载文案示例

| 状态 | 示例文案 |
|------|----------|
| 模型未加载 | 尚未找到模型产物。请在项目根运行 `python scripts/run_all.py` 后刷新。 |
| 分群缺失 | 分群结果未生成。请运行分群脚本或完整流水线。 |
| Agent 无 Key 降级 | 当前为模板模式：仍可调用分析工具，但自然语言编排能力有限。 |
| Pi 未安装 | 项目内 Pi SDK 未就绪。请运行 `python scripts/setup_pi_cli.py`（不会使用你电脑上的全局 pi）。 |
| 网络失败 | 无法连接后端，请确认 API 已在 :9800 启动。 |

---

## 19. 与后端联调检查清单

```text
□ VITE_API_BASE_URL 指向正确
□ /health 绿点
□ 总览数字与 /data/overview 一致
□ 模型表 PR-AUC 与 /models/metrics 一致
□ 预测展示 threshold 与 run_id
□ SHAP 条与 top_features 一致
□ Agent 能展开 tool_trace；render_chart 成功条目内联 ChartCard
□ Runtime 切换失败有中文原因；pi_fallback 显示降级 tag
□ 免责声明出现在分群/规则/Agent/大屏页脚
□ 无 Key 时页面不白屏
□ /screen 口径徽章文案与后端 caliber 字段一致
```

---

## 20. 设计变更流程

1. 改路由/视觉 token/组件契约 → 更新本文版本与对应节（令牌改动同步 `docs/plans/Design Tokens.md`）
2. 追加 `CHANGE.md`
3. 若影响后端字段 → 同步 `AGENTS.md` API 节
4. 更新 `pen/ui.pen` 对应样张
5. 再改 `frontend/` 代码

---

## 21. 附录 A：旧令牌迁移映射（v0.5 → v0.6）

前端代码当前仍持旧 Element 调色板（`tokens.css` / `chartTheme.ts`），须按下表迁移至 §6 令牌体系（迁移作为独立 `refactor(frontend)` 提交，避免与功能改动混杂）：

| 旧值（现 tokens.css / chartTheme.ts） | 新令牌 | 说明 |
|---|---|---|
| `--color-bg: #F5F7FA` | `--bg-page: #F8FAFC` | 页面底偏冷灰 |
| `--color-surface: #FFFFFF` | `--bg-card` | 不变 |
| `--color-border: #E4E7ED` | `--border-default: #E2E8F0` | |
| `--color-text: #303133` | `--text-body: #334155` | |
| `--color-text-secondary: #909399` | `--text-secondary: #64748B` | 旧值过浅，提深保投影可读 |
| `--color-primary: #409EFF` | `--color-primary-500: #3B82F6` | Element 覆盖 + chartTheme 同步 |
| `--color-primary-soft: #ECF5FF` | `--color-primary-50: #EFF6FF` | |
| `--color-success: #67C23A` | `#22C55E` | |
| `--color-warning: #E6A23C` | `#F59E0B` | |
| `--color-danger: #F56C6C` | `#EF4444` | |
| `--color-shap-pos: #409EFF` | `--chart-1` | |
| `--color-shap-neg: #F56C6C` | `--color-danger` | |
| 6 色图表序列 `#409EFF/#67C23A/#E6A23C/#F56C6C/#909399/#B37FEB` | 8 色 `--chart-1..8`（§6.1） | `chartTheme.CHART_COLORS` 整组替换 |
| `--header-height: 56px` | `--layout-header-height: 64px` | |
| `--sider-width: 200px` | `--layout-sidebar-width: 240px` | |
| `--content-max-width: 1280px` | `--layout-content-max: 1440px` | |
| `--font-sans: Segoe UI 栈` | `--font-family-base: Inter 栈` | Inter 经 CDN/系统回落 |
| `--font-mono: IBM Plex Mono` | `--font-family-number` / `--font-family-code` 两职分离 | 数字与代码字体分轨 |
| 无动效令牌（全仓硬编码 transition） | `--motion-duration-*` 三档 | 新增 |

**迁移顺序：** tokens.css 先行（定义新令牌 + 保留旧名别名指向新值）→ chartTheme.ts 对齐 → 逐页删除裸值 → 删除旧别名 → CHANGE 记录。别名过渡期保证视觉不回退。

---

## 22. 附录 B：`pen/ui.pen` 参考库

`pen/ui.pen` 为本设计系统的**可交互视觉真相**，内容结构：

1. **设计令牌样张**：全部色板磁贴、字阶、间距/圆角/阴影样例（与 §6 逐值一致）
2. **组件库**：§7 全部业务组件的精细样张（状态齐全：default/hover/focus/disabled/error；变体齐全：按钮 7 态、输入 5 态、标签 6 色、告警 4 类…）
3. **十路由整页样张**：`/screen`（暗色作用域）+ 工作台九页，含真实数据示例（8,000 样本、87.65% 正类、五渠道、E0–E8 矩阵）

**规则：** 视觉改动先改 .pen 再改代码；.pen 中组件命名与 §7.2 组件名一致；.pen 经 Pencil 工具访问（加密文件，禁止 Read/Grep 直读）。

---

## 23. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.6.0** | **2026-07-31** | **基于 Design Tokens v1.0 完全重构**：风格定调浅色·明亮·细腻·现代；§6 九类令牌全量收编（主色 `#409EFF`→`#3B82F6` 系、8 色图表序列、数字/代码字体分轨、动效三档、布局 240/64/64/1440/24）；§6.10 大屏作用域令牌收编；§21 旧→新迁移映射表；§22 `pen/ui.pen` 升为整页样张库 |
| v0.5.0 | 2026-07-31 | Stage 2–6：BaseChart 封装与色板单一真相；`/screen` 作用域暗色大屏；ChartCard spec 驱动内联渲染；侧栏四层叙事分组 + 折叠 + 路由轻 fade；叙事降级（反事实折叠、E4/E6 展示降权） |
| v0.3.0 | 2026-07-30 | 阶段9：9 路由（+`/simulate` `/pi`）；模型实验室全图化；客户页反事实；分群对比/投影/稳定性；Agent 五段渲染 + RuntimeBadge/ToolTracePanel；chartTheme 统一图表色 |
| v0.2.0 | 2026-07-30 | 收窄为前端专用；架构/后端迁入 AGENTS.md |
| v0.1.0 | 2026-07-30 | 初版（含全栈设计，已废止该形态） |

---

**一句话：** `DESIGN.md` 管「看起来与点起来是否一致、专业、可演示」；令牌以 §6 为唯一真相，样张以 `pen/ui.pen` 为视觉真相；「算得对不对、架构合不合理」以 `AGENTS.md` 为准。
