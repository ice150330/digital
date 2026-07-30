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
