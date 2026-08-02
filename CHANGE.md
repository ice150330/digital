# CHANGE.md — 项目变更记录

> **维护方式：** 人工追加（最新在上）。  
> **何时必记：** 功能、修复、约束/设计变更、依赖、计划决策、安全相关。  
> **与 git：** 不强制一条 commit 一条 CHANGE，但有意义改动不得省略；有 commit 时尽量填写哈希。  
> **权威约束：** 详见 `AGENTS.md` §11。

---

## 条目模板（复制使用）

```markdown
## YYYY-MM-DD — 简短标题

- **类型：** feat | fix | docs | refactor | chore | design | security
- **范围：** 模块或路径
- **摘要：** 做了什么
- **原因：** 为什么做
- **影响：** 对用户/开发/答辩/指标的影响
- **破坏性：** 无 | 有（说明迁移方式）
- **关联：** 计划/issue/commit（可选）
- **验证：** 跑过什么 / 未跑什么
```

---

## 变更日志

## 2026-08-02 — Halo 浅色大屏与视觉系统第一批全量重构

- **类型：** design / refactor / docs
- **范围：** `frontend/src/{views,styles,utils,components,router,App.vue}`、`pen/ui.pen`、`DESIGN.md`、`docs/plans/Design Tokens.md`、`AGENTS.md`
- **摘要：**
  - 前端主题从 v1 蓝色/暗色大屏口径切换到 Halo v2 浅色圆角工作台：主色 `#5749f4`、浅色页面背景、24px 卡片圆角、40px 大面板圆角与统一阴影
  - `/screen` 不再通过 `meta.fullscreen` 绕开 `AppLayout`，重构为工作台内的中央转化星图：ECharts graph 居中，外圈十个业务图标徽章串起数据、模型、解释、分群、规则、预算与 Pi 状态
  - 图表主题去掉独立 `screen` 分支，`GraphChart` 纳入 ECharts 注册，所有图表统一使用浅色 `chartTheme`
  - 补齐 ECharts `GraphicComponent` 注册，内收外圈徽章位置，移动端 `screen`、Tag、RunIdChip、AppLayout 主区增加收缩约束；业务卡片容器统一升到 `--radius-card`
  - `pen/ui.pen` 已同步 Halo v2 变量与 Design Tokens 画布；组件库与 `/screen` 画布仍需通过 Pencil 执行器继续收口
  - `DESIGN.md` 与 `docs/plans/Design Tokens.md` 升版到 Halo v2，明确 `/screen` 并入 AppLayout、中央星图、外圈小图标、浅色默认主题和接口取数红线
- **原因：** 执行 `docs/plans/2026-08-02-Halo风格全量视觉改造计划.md`，落实用户要求的“大图表居中、围一圈小图标、页面不再与整体框架分开、默认浅色系、ui.pen 与文档同步”。
- **影响：** 答辩开场从旧拼版暗色大屏切换为浅色 Halo 工作台大屏；文档、运行时 token、图表主题开始同源收敛。
- **破坏性：** 无（前端路由仍为 `/screen`，API 契约不变）
- **关联：** `docs/plans/2026-08-02-Halo风格全量视觉改造计划.md`
- **验证：** `cd frontend; npm run build` 通过（仅 Vite chunk >500 kB 非阻塞警告）；`pytest tests/test_openapi_routes.py tests/test_agent_tools.py` 通过（22 passed，1 个第三方 deprecation warning）；`frontend/src` 静态搜索确认无 `meta.fullscreen`、`data-theme="screen"`、`chartColors('screen')`、`axisTheme('screen')` 残留；本地 API 9800 + Vite 5600 下用 Chrome headless 截图检查 `/screen` 桌面与 390px，CDP 量测 390px `docScrollWidth=docClientWidth=375`，顶部栏和侧栏可见。

## 2026-07-31 — 前端全量重构 Stage 1–5：组件库、真实流式与会话管理落地

- **类型：** feat / refactor / design
- **范围：** `frontend/`、`src/digital_marketing/{agent,api,schemas}/`、`tests/`、`AGENTS.md`、`DESIGN.md`、重构计划
- **摘要：**
  - 按 `pen/ui.pen` 与 Design Tokens v1.0 对齐全局令牌、Element Plus 覆盖、工作台布局和 `/screen` 专用暗色变量
  - 接入 `@iconify/vue` Unicons 薄封装，新增 Button/Tag/KpiCard/StatStrip/Disclaimer/Agent 会话与工具时间线组件
  - Agent 页面接入 `POST /agent/chat/stream` 真实 SSE：文本增量、工具开始/结束、图表、五段契约、完成与错误事件实时呈现，并支持停止生成
  - 新增会话摘要列表与可恢复软删除 API；前端支持历史会话搜索、新建、切换与删除，Pi 控制台显式展示 SDK 桥接状态
  - 补齐 ConversionDonut、QualityIssueRow、SegmentCard、RuleRow、RunIdChip、PredictResultCard、LoadingState、CodeBlock 等业务组件；图表主题统一从 `chartTheme.ts` 与 tokens 取色
  - 浏览器视觉验收修复 Iconify CSS 变量尺寸失效、ECharts 漏注册 PieChart、Agent 流式回调绕过 Pinia 响应式对象、390px 三栏溢出与深色代码块样式污染
- **原因：** 将前端从 Element Plus 默认样式收束为设计样张中的浅色分析工作台，并把 Agent 体验提升为答辩主路径。
- **影响：** 新增三个 P1 Agent 契约：`POST /agent/chat/stream`、`GET /agent/sessions`、`DELETE /agent/sessions/{session_id}`；前端新增 Pinia 状态管理与 Iconify 依赖。
- **破坏性：** 无
- **关联：** `docs/plans/2026-07-31-前端全量重构计划.md` 阶段 1–5；`pen/ui.pen`
- **验证：** `pytest -q`：**118 passed, 1 skipped**；Agent/OpenAPI 定向回归 **22 passed**；`npm run build` 通过（仅 ECharts/入口 chunk >500 kB 非阻塞警告）；Chrome CDP 验证十路由、侧栏折叠、阈值滑块、单条/批量预测与 SHAP、预算模拟、真实 SSE（2 工具 + 1 图表 + 3 契约块）、历史会话、一键报告和 API 断线中文错态；390px `scrollWidth=390`。

## 2026-07-31 — CLAUDE.md 改进：测试命令、runtime 口径与令牌源引用

- **类型：** docs
- **范围：** `CLAUDE.md`
- **摘要：**
  - 校准 pytest 计数为 **115 passed，1 skipped**（原 114 passed）
  - 在「常用命令」中补充单条/关键字测试写法：`pytest tests/test_api_core.py::test_health -v`、`pytest -k "predict or explain" -v`
  - 权威文档表新增 `docs/plans/Design Tokens.md` 作为设计令牌源
  - 澄清 Pi runtime 默认来源：`config/agent.yaml` 默认 `pi`，`.env.example` 中的 `DIGITAL_AGENT_RUNTIME=local` 仅作覆盖示例
- **原因：** `/init` 技能要求持续维护 CLAUDE.md；避免新实例误读默认 runtime、遗漏单测命令、不知令牌文档源
- **影响：** 后续 Claude Code 实例启动更快、口径更准确
- **破坏性：** 无
- **验证：** `pytest` 115 passed，1 skipped；CLAUDE.md 链接与引用已核对

## 2026-07-31 — DESIGN.md v0.6.0：基于 Design Tokens v1.0 完全重构 + pen/ui.pen 整页重建

- **类型：** design / docs
- **范围：** `DESIGN.md`、`docs/plans/Design Tokens.md`（引用为令牌源）、`pen/ui.pen`
- **摘要：**
  - DESIGN.md 完全重构至 **v0.6.0**：风格定调「浅色 · 明亮 · 细腻 · 现代」；§6 九类令牌全量收编（品牌主色 `#409EFF`→`#3B82F6` 系、8 色图表序列 `--chart-1..8`、语义化别名 `--bg-*/--text-*/--border-*`、Inter/数字/代码三轨字体、动效三档 150/250/400ms、布局 240/64/64/1440/24、大屏 `[data-theme=screen]` 作用域令牌）；新增 §21 旧→新迁移映射表（tokens.css / chartTheme.ts 的独立 `refactor(frontend)` 迁移路径）与 §22 pen/ui.pen 参考库约定
  - pen/ui.pen 清空重建：设计令牌样张 + 组件库（状态齐全的可复用组件）+ **十路由整页样张**（含 `/screen` 暗色大屏），使用真实数据口径（8,000 样本 / 87.65% 正类 / 五渠道 / E0–E8 矩阵）
- **原因：** 旧视觉为 Element Plus 默认调色板（观感平板），用户要求参考新 Design Tokens 文件重构设计文档并重建「足够细节」的组件参考库
- **影响：** DESIGN.md 成为新令牌体系的前端权威；**前端代码尚未迁移**（仍持旧色板），按 §21 映射表作为独立后续提交执行，别名过渡保证不回退；CLAUDE.md 中 `pen/ui.pen`「非整页」表述随之过时，本次一并更正
- **破坏性：** 无（纯文档 + 设计资源；运行时行为不变）
- **验证：** DESIGN.md 令牌表与 `docs/plans/Design Tokens.md` §10 CSS 逐值核对；pen 逐屏截图自查（见后续条目补录）

## 2026-07-31 — Stage 5：Pi 真实编排桥接（VibeStart 范式：同进程 SDK + customTools 宿主代理）

- **类型：** feat
- **范围：** `tools/pi-cli/bridge/chat.mjs(新)`、`agent/pi_runtime.py`、`agent/local_runtime.py`、`agent/tools/{__init__.py,catalog.py}`、`api/routes_agent.py`、`schemas/agent.py`、`scripts/setup_pi_cli.py`、`tests/test_pi_bridge.py(新)`、`AGENTS.md`
- **摘要：**
  - **学习 VibeStart（F:\Project\VibeStart）的 pi 接入范式**并适配本项目：`createAgentSession` 同进程 SDK + `defineTool` customTools + `ExtensionFactory`（before_agent_start 注入宿主接地指令）+ `session.subscribe` 事件流
  - `tools/pi-cli/bridge/chat.mjs`：Node 桥接（stdin 请求 / stdout JSONL：ready/tool_start/tool_end/done/error）；每个 customTool 的 execute 是**代理**——HTTP loopback 回宿主 `POST /agent/tool-run` 由 Python REGISTRY 实算（§9.1 红线：数字永不出宿主，Pi 只编排与叙述）
  - `@tool` 装饰器扩 `description`/`parameters`（JSON Schema），19 个工具全部声明；新端点 `GET /agent/tools/manifest`（桥接工具清单，宿主声明为唯一真相）+ `POST /agent/tool-run`（loopback 执行口）
  - `pi_runtime.run_pi_chat` 实装：pi_status 增 bridge_ready 三要素检测（脚本/node/SDK 包）；spawn 桥接 → 解析 JSONL → grounding 装配五段契约 → 审计落盘；**任何失败（node 缺失/包未装/超时/无工具调用）自动降级 local**，`pi_fallback` + `open_questions` 契约不变；`persist_turn` 提取为 local/pi 共用
  - `setup_pi_cli.py`：默认安装 `@earendil-works/pi-coding-agent` + `typebox`；package.json `type=module`
- **原因：** 用户确认「安装真实 Pi」决策 + 指定参考 VibeStart 的接入方式；桥接范式比 CLI 子进程更稳（同进程 SDK、结构化工具协议、Pi 原生 customTools 机制天然契合宿主接地红线）
- **影响：** 装完 SDK + LLM Key 后 runtime=pi 即为真实 Pi 编排；未装时行为与之前完全一致（stub 降级）
- **破坏性：** 无（try_pi_or_fallback 别名保留，既有降级链测试零修改通过）
- **验证：** `pytest` 全量 **115 项绿**（+10 桥接测试：manifest/tool-run 端点、事件装配五段契约、无工具调用拒绝装配、降级链 ×3）；`node --check bridge/chat.mjs` 语法通过；**桥接真实联通待用户安装 SDK 后实测**（Stage 5d）

## 2026-07-31 — Stage 6：侧栏四层叙事分组 + 叙事降级 + 交互动效 + 文档总升版

- **类型：** feat / design
- **范围：** `frontend/src/layouts/AppLayout.vue`、`views/{CustomersView,ModelsView}.vue`、`App.vue`、`style.css`、`DESIGN.md`(v0.5.0)、`AGENTS.md`(v0.6)
- **摘要：**
  - 侧栏重构为**五组叙事分组**：总览大屏 → 描述性分析 → 预测建模 → 深度挖掘 → AI 与系统，显式呈现「数据分析→数据挖掘由浅入深」；首用 @element-plus/icons-vue（图标均带 title）；**兑现 DESIGN §3.2 折叠欠账**（200↔64，transition 0.18s，<992px 自动图标栏）
  - **叙事降级（仅前端呈现层，代码/端点完整保留）：** CustomersView 反事实面板收进 ElCollapse 默认收起（标题注「模型行为分析（敏感性），非因果」）；ModelsView E4 SMOTE / E6 flag 消融行 `muted-row` 弱化 + 「展示降权」tag；**E5 泄漏消融、E7 Stacking、E8 校准、多算法分群对比保持主线**（用户确认）
  - 路由切换轻 fade（150ms out-in，`prefers-reduced-motion` 关）——治理「全仓 0 transition」
  - 文档总升版：DESIGN v0.5.0（§3.2 折叠实现、§20 版本记录）；AGENTS v0.6（头部同步说明、§13 实现状态刷新：十路由/图表工具/Pi 侦察锁定）
- **原因：** 落实重构计划 Stage 6 与用户精简清单（反事实 + E4/E6 两项叙事降级）
- **影响：** 答辩动线：大屏开场 → 描述性 → 预测建模 → 深度挖掘 → AI 与系统；降级项演示时手动展开即可
- **破坏性：** 无（Pinia 本轮仍不引入：折叠态为组件本地状态，无需跨组件共享）
- **验证：** `pytest` 全量 **105 项绿**（94 基线 + 6 dashboard + 5 render_chart）；`npm run build` 绿；待人工目检答辩动线（DESIGN §18 清单）

## 2026-07-31 — Stage 4：render_chart 声明式图表工具 + /agent 内联 ChartCard（AI 会话生成图表）

- **类型：** feat
- **范围：** `agent/tools/catalog.py`（唯一实现点，装饰器注册实证）、`config/agent.yaml`（whitelist +1）、`frontend/src/components/ChartCard.vue(新)`、`frontend/src/views/AgentView.vue`、`tests/test_agent_tools.py`、`AGENTS.md`、`DESIGN.md`
- **摘要：**
  - `render_chart` 工具：chart_type 白名单（bar/line/pie/scatter/heatmap/funnel）× dataset 白名单 9 项（渠道/类型转化、leaderboard PR-AUC、年龄/收入/支出分布、分群规模、lift 十分位、全局 SHAP），宿主从 SQLite/产物计算真实数据 → 返回 **chart-spec v1.0 纯 JSON**（含 caliber/source/disclaimer）；越界 VALIDATION_ERROR
  - 关键词规划按消息推断 dataset（"画各渠道转化率柱状图"→conversion_by_channel；"画分群规模占比饼图"→pie/segment_sizes）；facts 抽取器**只述存在性不重复数字**（数字在图里）
  - 前端 `ChartCard.vue`：spec→option 映射（bar/line/pie，长类目自动横向，色板走 chartTheme 单一真相），caliber/disclaimer 脚注，未知图型兜底不崩；AgentView 对 render_chart 成功 trace 条目内联渲染，示例 chips +3
- **原因：** 用户需求「制作图表工具，让 AI 在会话中生成前端各种图表」；Stage 1 装饰器使新工具真正只改 catalog.py 一处（白名单配置 +1 除外）
- **影响：** /agent 可对话出图；红线：LLM/Pi 永不产 spec，spec 永由宿主工具产出（AGENTS §9.1 补录）
- **破坏性：** 无
- **验证：** `tests/test_agent_tools.py` +5 项（纯 JSON 序列化、9 数据集、白名单拒绝、facts 无数字、规划路由）共 25 项绿

## 2026-07-31 — Stage 3：L1 描述性后端 + /screen 全屏大屏（数据分析→数据挖掘开场全景）

- **类型：** feat
- **范围：** `services/dashboard.py(新)`、`schemas/data.py`、`api/routes_data.py`、`frontend/src/{views/ScreenView.vue,styles/screen.css,api/data.ts,router/index.ts,App.vue}`、`frontend/index.html`、`tests/test_api_dashboard.py(新)`、`AGENTS.md`、`DESIGN.md`
- **摘要：**
  - 新端点 `GET /data/dashboard`（KPI 聚合 + 伪漏斗四阶段 + 年龄/收入/AdSpend 10 等宽箱直方图 + caliber 口径字段）与 `GET /data/cross-matrix`（维度白名单 channel/type/gender，越界 422），走 SQLite 主数据轨只读 SQL
  - `/screen` 全屏大屏（`meta.fullscreen` 绕过 AppLayout）：KPI 磁贴 ×6、行为伪漏斗、渠道转化、渠道×类型热力、分布 ×3、E0–E8 mini 榜、SHAP Top8、页脚 caliber + 免责声明；`data-theme="screen"` 作用域暗色（深蓝分层底 + 8 色数据色板 + Rajdhani 数字字体 CDN swap 离线回退）；板块独立请求独立降级，不造假数
  - **口径红线：** 伪漏斗为横截面独立计数、非 cohort、阶段不嵌套——故用柱状图而非漏斗形（实测 converted=7012 > deep_visited=7011，漏斗形会乱序误导）；数据无时间字段，时序永不做；caliber 后端产出前端原样渲染
- **原因：** 落实重构计划 Stage 3 与用户决策（新增 /screen、L1 全补），补齐四层叙事中最薄的描述性分析层，答辩开场有全景冲击页
- **影响：** 导航 9→10 路由；补上 L1 坡度（漏斗/分布/交叉/KPI）；DESIGN §3.1/§3.3/§5.6/§10.10 与 AGENTS §10.2/§10.3 同步
- **破坏性：** 无
- **验证：** `tests/test_api_dashboard.py` 6 项绿（漏斗计数与手工 SQL 一致、白名单 422、空表 404）；`npm run build` 绿；真实 8000 行库烟测：KPI/漏斗/20 交叉单元全部正确

## 2026-07-31 — Stage 2：前端图表基建 + 样式收敛（BaseChart + 色板单一真相 + 裸 hex/内联样式清零）

- **类型：** refactor
- **范围：** `frontend/src/components/{BaseChart.vue(新),10 个图表组件,ToolTracePanel.vue}`、`frontend/src/utils/{echarts.ts(新),chartTheme.ts}`、`frontend/src/styles/tokens.css`、`frontend/src/{style.css,layouts/AppLayout.vue,views/*}`、`DESIGN.md`
- **摘要：**
  - 新增 `BaseChart.vue`：init/ResizeObserver（容器级，替代 window resize）/dispose/watch 集中承接，10 个图表组件样板归零，仅保留 `computed option`；ECharts 按需注册集中到 `utils/echarts.ts`（+Funnel/Title 供 Stage 3）
  - `chartTheme.ts` 修漂移（CHART_COLORS[5] `#9b59b6`→`#b37feb`、COLOR_TEXT `#606266`→`#303133` 对齐 tokens）；新增 `chartColors(theme)`/`axisTheme(theme)`/COLOR_SURFACE/COLOR_HEAT_LOW，screen 分支运行时读 `--screen-chart-1..8`
  - 裸 hex 清零：AppLayout 状态色改 `var()` 内联、tokens 新增 primary-soft/hover/code-bg/warning-soft/code-dark 系列；ShapBar/ChannelBar/ConfusionHeatmap 硬编码改 chartTheme 常量
  - 44 处内联 style 收敛为 8px 网格工具类（ml/mr/mt/mb/w-full/input-wide/flex-1，off-grid 12px 归一到 8px），仅保留 2 处控件固定宽度与动态 :style 绑定；图表高度收敛 280/320 两档
- **原因：** 落实重构计划 Stage 2，为 Stage 3 大屏（BaseChart screen 主题 + 色板作用域）与 Stage 4 ChartCard 铺底座；治理双份色板漂移与样式碎片
- **影响：** 视觉无感知变化（option 内容逐字未动）；侧栏折叠/窗口缩放图表自适应；DESIGN §8.0 立封装与色板规矩
- **破坏性：** 无
- **验证：** `npm run build`（vue-tsc + vite）通过；待人工目检 9 路由图表与间距（清单见 DESIGN §18）

## 2026-07-31 — Stage 1：后端结构重构（配置统一 + 工具装饰器 + 分发上提 + 运行时缓存）

- **类型：** refactor
- **范围：** `agent/{config.py(新),tools/__init__.py,tools/facts.py(新),tools/catalog.py,grounding.py,local_runtime.py,pi_runtime.py,service.py,audit.py}`、`api/routes_agent.py`、`services/artifacts.py`、`scripts/{02,06}`、`tests/test_agent_config.py(新)`、`AGENTS.md`
- **摘要：**
  - 新增 `agent/config.py`：pydantic `AgentConfig` 统一加载 `agent.yaml`（lru_cache + `set_runtime_persisted` 写回失效）；local_runtime/pi_runtime/audit/routes_agent 四处重复 `yaml.safe_load` 收敛为一处
  - 工具注册改 `@tool(...)` 装饰器（`ToolMeta`：keywords/base_kwargs/plan/facts/plan_order/stage）：新增工具只改 `catalog.py` 一处定义，REGISTRY/关键词规划/grounding 事实分派/whitelist 校验自动生效；`grounding.facts_from_tool` 17 分支逐字搬迁至 `tools/facts.py`，入口签名不变（report.py 无感）
  - runtime 分发上提 `service.chat`（pi → `pi_runtime.run_pi_chat`，其余 → local）；`run_local_chat` 删除内埋 pi 分支；`try_pi_or_fallback`/`plan_tools` 保留兼容别名，旧测试零修改
  - `artifacts.load_runtime` / clean.csv 全表加 lru_cache（缓存键含产物根路径，防测试 monkeypatch 跨根污染）；训练脚本 02/06 结尾 `clear_runtime_cache()`
- **原因：** 落实 2026-07-31 重构计划 Stage 1——消除「新增工具六处手工联动」、runtime 分发错位与重复模型加载，为 Stage 4 图表工具（一处定义实证）与 Stage 5 Pi 真实协议铺路
- **影响：** 行为零变化（plan 顺序/去重/[:6]/默认兜底/facts 文本逐字一致）；新增工具成本从 6 处降至 1 处；predict_batch 热路径不再重复 joblib.load
- **破坏性：** 无（`try_pi_or_fallback`、`plan_tools`、`facts_from_tool` 旧入口均保留）
- **验证：** `pytest` 全量（含新增 test_agent_config.py 8 项：默认值/缓存/写回/whitelist/注册完备/规划回归）；修复一处缓存键无路径导致的测试间污染

## 2026-07-30 — 阶段9：算法深化 + Pi 编排中枢（红线内拉满）

- **类型：** feat
- **范围：** `models/`、`explain/`、`segment/`、`simulate/`（新）、`agent/`、`api/`、`schemas/`、`services/artifacts.py`、`config/{model,agent}.yaml`、`scripts/06–09`、`agent/skills/`、`frontend/`、`tests/`
- **摘要：**
  - **训练深化（W9a）：** 实验矩阵扩至 E0–E8（E2 默认树、E4 SMOTE、E5 +ConversionRate 泄漏消融、E6 去质量 flag 消融、E7 Stacking 5-fold OOF、E8 Platt/Isotonic 校准 valid 择优）；每 run 落 CV 5-fold（仅 train）、test bootstrap 95% CI、PR/ROC 曲线、lift 十分位、成本敏感阈值扫描；per-run transformer；消融 run 代码级排除默认 run 参选
  - **分析深化（W9b）：** PDP/ICE、反事实（单特征曲线 + 贪心最小改动，强制「模型行为≠因果」disclaimer）、多算法分群（KMeans/GMM/Agglomerative × K + silhouette/CH/BIC + bootstrap ARI 稳定性 + PCA 投影 + z-score 自动画像名）、预算模拟器（期望值口径，K 扫描 + 推荐 K + Top-K 名单 CSV）
  - **API + 工具（W9c）：** +10 端点（curves/calibration/lift/threshold-scan/pdp/counterfactual/segments compare+projection/simulate budget/audit recent/agent report）；+6 Agent 工具（compare_experiments、get_calibration_summary、get_lift_table、simulate_budget、counterfactual_explain、generate_analysis_report），五处联动
  - **Pi 编排中枢（W9d）：** `agent.yaml` 默认 `runtime: pi`；stub 检测（读文件头 pi-stub 标记）+ 明确降级 local（响应 `pi_fallback` + open_questions 标注）；skills ×7（frontmatter + 编排步骤 + 口径红线）；一键分析报告落盘 `outputs/reports/analysis_<ts>.md`；audit.py 真正消费 agent.yaml
  - **前端（W9e）：** 路由 7→9（+`/simulate` `/pi`）；`/models` 全图化（CV/CI/Brier 列 + PR/ROC 双联 + 校准 + 混淆热力 + lift + 阈值-成本滑块）；`/customers` 反事实面板；`/segments` 自动画像名 + 稳定性徽章 + PCA 散点 + 多算法对比；`/agent` 五段契约渲染 + RuntimeBadge/ToolTracePanel 组件化；新组件 ×10；`chartTheme.ts` 统一图表色
  - **收尾（W9f）：** `run_all.py --full` 串联 06/07/08/09；论文表导出扩 CV/CI/Brier/ablation 列；AGENTS/DESIGN/README/CLAUDE 同步
- **原因：** 用户要求 8k 数据用到极致的「最复杂、算法最丰富」系统并强化 Pi runtime 核心地位；已确认「红线内拉满（不做 uplift 因果主线）+ Pi 编排中枢」两项决策
- **影响：** 实验结论更丰富也更诚实（E5 泄漏消融 roc 0.811 vs E3 0.792 证明泄漏增益有限；E8 校准 ECE 0.1126→0.0193）；默认 run 仍为 E2_lightgbm_default（解释友好）；答辩可演示预算模拟与一键报告
- **破坏性：** 有（`agent.yaml` 默认 runtime 由 local 改为 pi；stub/未安装时行为为降级 local 并标注，与旧 local 行为等价）
- **关联：** 计划 `~/.claude/plans/breezy-snuggling-teacup.md`（阶段9 六波次）
- **验证：** `pytest` 86 passed（新增 test_train_full/test_simulate/test_counterfactual/test_api_advanced/test_agent_runtime 等）；`npm run build` 通过；`scripts/06/07/08/09` 全量跑通落盘；`export_paper_tables.py` 9 行
- **未做：** uplift 因果主线、SHAP interaction（NumPy2 环境冲突史，回退跳过）、真 Pi 实装联调（本机 stub；真装路径已有 --help 探测分支）

## 2026-07-30 — 包 docstring 去占位残留

- **类型：** chore / docs
- **范围：** `src/digital_marketing/{features,models,explain,data}/__init__.py`
- **摘要：** 模块说明与实现对齐，去掉脚手架阶段的「占位」表述
- **原因：** 代码整理；避免阅读包入口时误判未实现
- **影响：** 无运行时行为变化
- **破坏性：** 无
- **验证：** 文案校对；工作树其余已与 origin/main 同步

## 2026-07-30 — 端口 9800/5600 + 阶段8 打磨

- **类型：** chore / docs / test
- **范围：** 端口配置、CORS、`scripts/demo_checklist.md`、`export_paper_tables.py`、OpenAPI/泄漏单测、README/AGENTS/DESIGN/About
- **摘要：**
  - API 默认演示端口 **9800**；Vite **5600**（`strictPort`）；CORS / `VITE_API_BASE_URL` / 文档全量对齐
  - 演示清单 8–10 分钟 + 失败预案；论文表从 `leaderboard.json` 导出 md+csv
  - 测试：特征无 CustomerID、OpenAPI 路径表、CORS 含 5600
- **原因：** 用户指定端口；全量计划阶段 8
- **影响：** 本地启动命令变更；旧 8000/5173 文档已替换
- **破坏性：** 有（开发端口变更；须用新端口启服务）
- **关联：** commit `af98337`
- **验证：** `python scripts/export_paper_tables.py`；`pytest` 38 passed；`npm run build`

## 2026-07-30 — docs：同步 README/AGENTS/计划至 P0+P1 终态

- **类型：** docs
- **范围：** `README.md`、`AGENTS.md`、`docs/plans/2026-07-30-全量前后端开发计划.md`、`CHANGE.md`
- **摘要：** 从零路径、脚本表、API 表、演示路径；AGENTS 复现命令与实现状态；计划状态改为阶段 0–7 已落地
- **原因：** 用户要求提交推送前同步文档
- **影响：** 新人/答辩可按 README 跑通；文档不再写「仅脚手架」
- **破坏性：** 无
- **关联：** commits `72b7080` `588d4f4` `9bec706` `7bb7663`（阶段 4–7）
- **验证：** 文档与代码命令对齐；`pytest` 此前 33 passed

## 2026-07-30 — 阶段7：batch 预测 + 项目内 Pi setup

- **类型：** feat
- **范围：** `services/artifacts.predict_batch`、`POST /models/predict/batch`、`scripts/setup_pi_cli.py`、`tests/test_pi_path.py`、客户页批量区、Agent chips
- **摘要：**
  - 批量预测上限 200，超限 422；部分失败记 `errors`
  - `setup_pi_cli.py` 写入 `tools/pi-cli/` stub（可选 `PI_NPM_PACKAGE`）；路径硬约束单测
  - 客户洞察页可逗号分隔批量预测
- **原因：** 全量计划 W7
- **影响：** 名单筛选演示 + Pi 可装可降级
- **破坏性：** 无
- **关联：** commit `7bb7663`
- **验证：** `python scripts/setup_pi_cli.py`；`pytest tests/test_api_core.py tests/test_pi_path.py`

## 2026-07-30 — 阶段6：K-Means 分群 + 关联规则 + API/页

- **类型：** feat
- **范围：** `segment/`、`rules/`、`api/routes_{segments,rules}.py`、`scripts/04_*`/`05_*`、`run_all --with-p1`、前端 Segments/Rules、Agent 工具扩展
- **摘要：**
  - 分群：训练特征不含 Conversion；summary + model.joblib + assignments；`GET /segments`、`POST /segments/assign`
  - 规则：mlxtend Apriori（失败则 pairwise 回退）；`GET /rules` 可筛 lift；Disclaimer 相关≠因果
  - Agent：`segment_summary` / `assign_cluster` / `top_association_rules` / `strategy_brief`
- **原因：** 全量计划 W6（P1）
- **影响：** 分群/规则页可真数据演示；run_all 默认仍 P0，`--with-p1` 可选
- **破坏性：** 无
- **关联：** `docs/plans/2026-07-30-全量前后端开发计划.md` W6；commit `9bec706`
- **验证：** `python scripts/04_train_cluster.py`；`05_mine_rules.py`；`pytest tests/test_segment_rules.py tests/test_agent_tools.py` 6 passed

## 2026-07-30 — 阶段5：LocalToolRuntime + Agent API/页

- **类型：** feat
- **范围：** `agent/`、`api/routes_agent.py`、`schemas/agent.py`、`frontend/.../AgentView.vue`、`tests/test_agent_tools.py`
- **摘要：** 白名单工具、五段契约+tool_trace、jsonl 审计与会话；`POST /agent/chat`；无 Key 走 template；Pi 路径校验占位
- **原因：** 全量计划 W5
- **影响：** 分析台可演示工具接地
- **破坏性：** 无
- **关联：** commit `588d4f4`
- **验证：** `pytest tests/test_agent_tools.py` 4+ passed

## 2026-07-30 — 阶段4：前端业务页 tokens 与七路由

- **类型：** feat
- **范围：** `frontend/` tokens、API 客户端、Home/Models/Customers/About、空态 Segments/Rules/Agent 壳
- **摘要：** Element Plus + ECharts 真数据联调 P0 四页；7 路由懒加载
- **原因：** 全量计划 W4
- **影响：** 演示路径总览→模型→客户可走
- **破坏性：** 无
- **关联：** commit `72b7080`
- **验证：** `npm run build`

## 2026-07-30 — 阶段3：SHAP/贡献解释 + P0 业务 API + run_all

- **类型：** feat
- **范围：** `explain/`、`services/artifacts.py`、`api/routes_{data,models,explain}.py`、`schemas/`、`scripts/03_explain_shap.py`、`scripts/run_all.py`、tests
- **摘要：**
  - 全局/局部解释：LightGBM `pred_contrib` 优先，TreeExplainer/线性 coef 代理回退（兼容本机 shap+matplotlib 与 NumPy2 冲突）
  - 产物门面 `services/artifacts.py`：overview、metrics、predict、explain
  - API：`GET /data/overview`、`GET /meta/features`、`GET /models/metrics`、`GET /models/metrics/{run_id}`、`POST /models/predict`、`GET /explain/global`、`POST /explain/customer`
  - `scripts/03_explain_shap.py`、`scripts/run_all.py`（clean→train→explain）
- **原因：** 全量计划阶段 3；先产物后 API
- **影响：** 前端可联调真指标/预测/解释；metrics 仍不进 SQLite
- **破坏性：** 无
- **关联：** `docs/plans/2026-07-30-全量前后端开发计划.md` W3
- **验证：** `python scripts/03_explain_shap.py`（默认 `E3_lightgbm_balanced` + `lightgbm_pred_contrib`）；`pytest` 22 passed
- **附：** `GET /health` 增 `artifacts_ok` / `default_run_id`；近并列 PR-AUC 默认偏好树模型

## 2026-07-30 — 全量前后端开发计划批准 + 第一刀开工

- **类型：** docs / feat
- **范围：** `docs/plans/`、`config/`、`src/digital_marketing/data|features|models/`、`scripts/`、`tests/`、`outputs/`、依赖
- **摘要：**
  - 落盘批准计划：`docs/plans/2026-07-30-全量前后端开发计划.md`（M0→答辩八波次）
  - 配置骨架：`config/features.yaml`、`model.yaml`、`agent.yaml`
  - 产物目录占位：processed/models/metrics/explain/segments/rules/agent_* /figures
  - 依赖：sklearn / lightgbm / joblib / numpy；可选 `[ml]` shap/mlxtend
  - **第一刀：** 数据 load/clean/quality/split + E0/E1/E3 训练与 metrics 落盘（见同日实现条目或本条续）
- **原因：** 用户批准全量计划；按「产物→API→UI」先做可复现数据与分类闭环
- **影响：** 后续 API/前端可消费 `outputs/metrics`；不扩大 P2
- **破坏性：** 无（增量）
- **关联：** 计划审批稿；深度计划 P0
- **验证：** `python scripts/01_clean_data.py`（8000 行，raw 未改）；`python scripts/02_train_classify.py`（E0/E1/E3）；`pytest` 14+ passed；leaderboard 含 pr_auc

## 2026-07-30 — Pencil 设计系统 v0.3 细化

- **类型：** design
- **范围：** `pen/ui.pen`
- **摘要：**
  - **Token 扩展：** `color-text-inverse`、图表序列 `color-chart-1..6`、概率色序 `color-proba-*`、`color-axis` / `color-code-*`；字号 `font-size-*`；布局 `header-height` / `sider-width` / `content-max-width` / `chart-height`；`space-2xl`、`radius-pill`
  - **01 Foundations：** 增补色板第三行 + 布局尺寸 token 卡片
  - **13 Forms Advanced：** Field/Number、Search、ThresholdSlider、Button/SampleFill·Predict、FormGroup/CustomerFeatures
  - **14 Tables Patterns：** TableHeaderCell、TableCell/*、TableToolbar、FilterBar、FilterChip、StatStrip、MiniTable/Rules
  - **15 Charts Extended：** PrCurveChart、RocCurveChart、MetricCompareBar、ProbaScale、ConfusionMatrix
  - **16 Business States About：** HealthDot/Degraded、RunIdChip、ThresholdNote、ProgressBar、StepIndicator、CodeBlock、DocLinkList、AiUsageNote
  - **00 映射表：** 追加上述组件 ↔ 前端路径行；页眉文案升为 v0.3
  - 修复 SHAP 负向条色绑定为 `$color-shap-neg`
- **原因：** 既有组件/配置不足以支撑后续业务页与 Agent UI 开发，对照 DESIGN 补齐缺口
- **影响：** 前端实现可对照更完整的原子件与 token；仍为设计资源库，非整页；不替代 `DESIGN.md`
- **破坏性：** 无代码；仅设计资源增补
- **关联：** `DESIGN.md` v0.2.0；既有 pen 库 v0.2
- **验证：** snapshot_layout 13–16 无裁切/重叠问题；Foundations / 映射表 / 四新区截图目视通过

## 2026-07-30 — 框架搭建 + SQLite 主数据 + Vue 空壳

- **类型：** feat
- **范围：** `src/digital_marketing/**`、`scripts/`、`tests/`、`frontend/`、`config/`、`pyproject.toml`、文档
- **摘要：**
  - 可安装包 `digital_marketing`：core（paths/config/logging）、data（SQLAlchemy 模型 + 同步 sqlite + CSV 导入）、api（CORS、request_id、`GET /api/v1/health` envelope）
  - **双轨存储：** CSV 真相 → `outputs/db/app.db`（`campaigns` / `import_batches`）；分析产物仍走 `outputs/` 文件，metrics **不进** SQLite
  - 脚本：`scripts/init_db.py`、`scripts/import_campaigns.py`；导入 8000 行通过
  - 测试：`pytest` 5 passed（import + health）
  - Vue3 空壳：Layout 健康点、侧栏占位、HomeView 联调 health；`VITE_API_BASE_URL`
  - 文档：AGENTS v0.3 双轨 + ADR SQLite；README 上手；CLAUDE 命令与状态更新
- **原因：** 用户确认第一步用 SQLite 存营销主数据，范围 = 后端骨架 + Vue 空壳
- **影响：** 后续清洗/训练/业务页可基于本骨架扩展；DB 可删库重建
- **破坏性：** 无（此前无业务实现）
- **关联：** 计划「第一步：框架搭建 + SQLite 初始化」
- **验证：** `pip install -e ".[dev]"`；import 8000 行；`pytest` 5 passed；`GET /api/v1/health` 返回 ok + campaigns_count=8000；`frontend npm run build` 通过。未在本机长期跑 `npm run dev` 浏览器手点（构建已过）

## 2026-07-30 — 新增 CLAUDE.md

- **类型：** docs
- **范围：** 仓库根目录 `CLAUDE.md`
- **摘要：** 为 Claude Code 会话提供精简入口：文档边界、目标命令、架构、数据/ML/Agent 红线、前端要点、改动纪律；细节指向 AGENTS/DESIGN/计划，不重复全文
- **原因：** `/init` 初始化仓库指引
- **影响：** 后续 Claude Code 实例优先读 CLAUDE.md 再下钻权威文档
- **破坏性：** 无
- **关联：** `AGENTS.md`、`DESIGN.md`
- **验证：** 文件已写入；当前仍无业务实现，命令为「目标形态」

## 2026-07-30 — Pencil 组件参考库 pen/ui.pen

- **类型：** design
- **范围：** `pen/ui.pen`
- **摘要：**
  - 在空 `ui.pen` 中建立**全量分类组件参考库**（非整页业务页面）
  - 设计 Token 对齐 DESIGN.md §5（色板 / 字体 Inter+IBM Plex Mono / 8px 间距 / 圆角）
  - 分类：00 映射表 · 01 Foundations · 02 Buttons · 03 Forms · 04 Tags · 05 Feedback · 06 Navigation Chrome · 07 Data Display · 08 Charts · 09 Agent · 10 Empty/Error · 11 Business · 12 Overlays & Tabs
  - 可复用组件约 84 个（KpiCard、ModelMetricsTable、ShapBarChart、AgentMessageList、ToolTracePanel、RuntimeBadge、EmptyState 等）
  - 含组件 ↔ 前端路径映射表，便于后续 Vue 实现
- **原因：** 用户要求用 Pencil MCP 设计项目可能用到的全量组件资源库，分类且尽量详细
- **影响：** 前端实现可直接对照组件库；不替代 DESIGN 文档约束
- **破坏性：** 无代码；仅新增设计资源
- **关联：** `DESIGN.md` v0.2.0
- **验证：** snapshot_layout 无问题；关键分区截图目视通过

## 2026-07-30 — 文档职责拆分：DESIGN 仅前端，架构/后端归 AGENTS

- **类型：** docs / design
- **范围：** `AGENTS.md`、`DESIGN.md`、本文件
- **摘要：**
  - **`DESIGN.md` 重写为前端专用**（v0.2.0）：技术栈、路由/布局、视觉 token、组件与图表、页面级约束、接口消费约定、空错态文案、联调清单
  - **`AGENTS.md` 升为开发+架构+后端权威**（v0.2）：硬禁止项、分层架构、数据/ML、API/DTO、Agent/项目内 Pi、配置安全测试、ADR
  - 明确冲突优先级与改动同步规则（UI→DESIGN，架构/API→AGENTS，契约字段两边都改）
- **原因：** 用户要求 DESIGN 聚焦前端详细设计约束，后端与架构类放入 AGENTS
- **影响：** 后续实现与 AI 改库按新分工阅读；旧「DESIGN=全栈设计」形态废止
- **破坏性：** 文档结构破坏性（读者路径变更）；无业务代码
- **关联：** 深度计划仍描述全栈，细节以 AGENTS/DESIGN 新分工为准
- **验证：** 两文件已重写落盘

## 2026-07-30 — 新增 AGENTS / DESIGN / CHANGE 三件套

- **类型：** docs
- **范围：** 仓库根目录 `AGENTS.md`、`DESIGN.md`、`CHANGE.md`
- **摘要：**
  - 新增 `AGENTS.md`：面向人类与 AI 代理的**强约束**（目录归位、指标纪律、数据泄漏红线、项目内 Pi 隔离、Agent grounding、git/CHANGE 纪律等）
  - 新增 `DESIGN.md`：完整系统设计（架构分层、数据与实验、API/DTO、Agent 与项目内 Pi、Vue 设计系统、配置/安全/测试/ADR）
  - 新增本文件：约定人工变更日志格式与首条记录
- **原因：** 支撑后续维护与开发；避免实现漂移和 AI 改库时破坏毕设约束
- **影响：** 此后所有有意义改动需读 AGENTS/DESIGN 并追加 CHANGE；实现阶段不得违背硬禁止项
- **破坏性：** 无（当前几乎无业务代码）
- **关联：** `docs/plans/2026-07-30-数字营销转化分析与AI-Copilot-深度计划.md`
- **验证：** 文件已写入仓库根目录；未运行训练/API（尚无实现）

## 2026-07-30 — 深度计划修订：项目内 Pi CLI

- **类型：** design / docs
- **范围：** `docs/plans/2026-07-30-数字营销转化分析与AI-Copilot-深度计划.md`
- **摘要：** Pi 改为由 `scripts/setup_pi_cli.py` 拉取到 `tools/pi-cli/`；禁止使用用户全局 `pi`；仅服务本项目本地
- **原因：** 用户明确要求项目自带 CLI、与本机全局 Pi 解耦
- **影响：** 后续 `PiRuntime`、验收与演示均以项目内路径为准
- **破坏性：** 无代码；设计约束生效
- **关联：** 计划书修订说明
- **验证：** 计划文档已更新

## 2026-07-30 — 深度计划落盘

- **类型：** docs
- **范围：** `docs/plans/`、`docs/reports/`
- **摘要：** 创建毕设第一版深度计划；建立 docs 目录结构
- **原因：** 固化题目、范围分层、架构、Agent/Pi、24 周里程碑与验收标准
- **影响：** 后续实现以该计划为范围基线
- **破坏性：** 无
- **关联：** —
- **验证：** 文档可读

## 2026-07-30 — 仓库初始化与数据就绪

- **类型：** chore
- **范围：** 仓库根、`data/`
- **摘要：** 初始 git 仓库、MIT LICENSE、空 README、Python `.gitignore`；数字营销转化 CSV 与数据说明
- **原因：** 项目起步
- **影响：** 从零工程骨架待建
- **破坏性：** 无
- **关联：** Initial commit
- **验证：** 数据文件存在于 `data/`
