# AGENTS.md — 开发约束 · 架构 · 后端权威

> **读者：** 人类开发者、Claude Code、Pi、Codex 及任何修改本仓库的自动化代理。  
> **职责划分（以用户约定为准）：**  
> - **本文件 `AGENTS.md`：** 开发/代理行为、**系统架构、后端、数据/ML、API、Agent/Pi、配置、安全、测试**  
> - **`DESIGN.md`：** **仅前端**（页面、视觉、组件、图表、交互、前端工程约束）  
> - **`docs/plans/*`：** 范围、优先级、里程碑  
> - **`CHANGE.md`：** 每次有意义修改的人工记录  
> **冲突优先级：** 硬性禁止项以本文件为准；前端视觉/交互以 `DESIGN.md` 为准；范围以计划书为准。  
> **语言：** 用户可见说明、文档、注释（非标识符）用**中文**。  
> **最后同步：** 2026-07-31（v0.6：重构计划 Stage 1–4/6 — agent 配置统一 + @tool 装饰器一处注册 + runtime 分发上提 + 运行时缓存；`/data/dashboard`+`/data/cross-matrix` 描述性端点（横截面口径）；`render_chart` 图表工具 + chart-spec v1.0；Pi 侦察报告锁定 A 主 B 兜底协议，真实编排待安装后落实）

---

## 0. 必读顺序（每次会话开工前）

1. 本文件 `AGENTS.md`（开发 + 架构 + 后端）  
2. 若改 UI：再读 `DESIGN.md`  
3. `docs/plans/` 最新深度计划  
4. `CHANGE.md` 最近条目  
5. 将改动的代码/配置  

**未读完本文件前，不得大规模改目录、换后端技术栈、接入全局 Pi 或改评价指标口径。**

---

## 1. 项目是什么

| 项 | 内容 |
|----|------|
| 名称 | digital（数字营销转化分析与 AI Copilot） |
| 类型 | 本科毕业设计：**算法与工程并重** |
| 数据 | `data/digital_marketing_campaign_dataset.csv`（约 8000×20，目标 `Conversion`） |
| 交付 | Python 挖掘管线 + FastAPI + Vue SPA + 系统内分析 Copilot |
| 非目标 | 生产多租户投放、因果 uplift 主线、K8s、用 LLM 当主分类器、调用用户全局 `pi` |

**一句话：** 可复现的转化预测与可解释分析系统，外加**工具接地**的分析 Agent；不是聊天壳，也不是纯 notebook。

---

## 2. 权威文档边界

| 文档 | 职责 | 可否被代码悄悄推翻 |
|------|------|-------------------|
| `AGENTS.md` | 禁止项、流程、**架构/后端/数据/ML/API/Agent** | **否** |
| `DESIGN.md` | **前端设计系统** | **否**（改 UI 规范须改 DESIGN + CHANGE） |
| `docs/plans/*` | 范围与里程碑 | 扩大 P2 须确认并记 CHANGE |
| `docs/reports/*` | 实验/质量报告 | 数字须可复现 |
| `CHANGE.md` | 变更日志 | 有意义改动必须追加 |
| `config/*.yaml` | 运行时配置 | 密钥不得入库 |
| `README.md` | 人类上手 | 与启动命令一致 |

**改动同步规则：**

- 改架构 / API / 数据协议 / Agent / Pi → **只改本文件**（+ CHANGE），不必塞进 DESIGN  
- 改页面结构 / 视觉 / 组件 / 图表交互 → **改 DESIGN**（+ CHANGE）  
- 前后端契约字段变更 → **本文件 API 节 + DESIGN 中「接口消费约定」** 同时更新  

---

## 3. 硬性禁止项（MUST NOT）

### 3.1 工程与目录

1. **禁止**把计划书、报告、临时脚本、模型大文件堆在仓库根目录（根目录允许项见 §5）。  
2. **禁止**未更新本文件就更换**后端**主栈（如 Django 替换 FastAPI）；未更新 `DESIGN.md` 就更换**前端**主栈（如 React 替换 Vue）。  
3. **禁止**提交 `.env`、API Key、令牌、含密钥的 notebook 输出。  
4. **禁止**把 `outputs/` 大模型、`tools/pi-cli/node_modules`、`frontend/node_modules` 强行入库。  
5. **禁止**覆盖 `data/` 下**原始** CSV；清洗结果写入 `outputs/processed/`（或配置中固定的 processed 目录）。  

### 3.2 机器学习与学术诚信

6. **禁止**仅用 **Accuracy** 作为主结论指标。主指标见 §8。  
7. **禁止** `CustomerID` 入模。  
8. **禁止**默认主实验把 `ConversionRate` 当普通特征且不做消融（主模型默认**不含**；含/不含仅 E5）。  
9. **禁止**先 fit 全量再划 test；**禁止**在 test 上调阈值。  
10. **禁止**伪造指标、手改 metrics 充论文表。  
11. **禁止**无依据的因果承诺或「已上线收益 xx」。  

### 3.3 Agent / Pi / LLM

12. **禁止**调用用户 PATH / 全局 `pi`；只允许 `tools/pi-cli/`（§9）。  
13. **禁止** LLM 无工具结果时编造 PR-AUC、转化率、SHAP 等数字。  
14. **禁止** Agent 默认可写原始数据或任意高危 shell；工具白名单。  
15. **禁止**用 LLM 替代主分类器。  
16. **禁止**把本项目 Pi 装到用户全局 npm 或改用户 shell 配置。  

### 3.4 协作与 git

17. **禁止**用户未要求时 `git commit` / `push` / 改 git config。  
18. **禁止**对主分支 force push、未确认删除他人工作。  
19. **禁止**大范围重构却不写 `CHANGE.md`。  

### 3.5 前后端分工

20. **禁止**在前端写死「最佳 AUC=0.xx」；必须请求后端 metrics。  
21. **禁止**在 `DESIGN.md` 中维护后端模块树/训练协议（应在本文件）；**禁止**在本文件写细视觉 token（应在 DESIGN）。  

---

## 4. 系统架构（后端权威）

### 4.1 上下文

```text
┌─────────────┐    HTTP JSON /api/v1/*    ┌──────────────────┐
│  Vue SPA     │ ◄──────────────────────► │  FastAPI          │
│  (见 DESIGN) │                          │  digital_marketing│
└─────────────┘                          └────────┬─────────┘
                                                  │
          ┌───────────────────────────────────────┼──────────────────────────┐
          ▼                       ▼               ▼                          ▼
   Analysis Core           Agent Service    SQLite 主数据轨           产物文件轨
清洗/特征/训练/SHAP       tools + LLM/Pi   outputs/db/app.db         outputs/{models,
分群/关联规则             audit            ← CSV 导入可重建           metrics,processed…}
          │                     │
          └──────────┬──────────┘
                     ▼
            tools/pi-cli/ (可选, 项目内)
```

### 4.2 设计原则

| 原则 | 含义 |
|------|------|
| 内核与 Agent 分离 | 指标/模型只来自分析内核 |
| **双轨存储** | **主数据轨** SQLite（查询/列表）；**产物轨** `outputs/` 文件（模型/metrics/SHAP） |
| 产物驱动 | 论文、API、Agent 共用 `outputs/` 分析产物；metrics **不进** SQLite |
| Runtime 可插拔 | 默认 `local`；`pi` 为项目内 CLI |
| 先正确后展示 | P0 保证指标与 API；UI 见 DESIGN |
| 相关非因果 | API 文案与 Agent 统一口径 |
| Pi 本地隔离 | 仅 `tools/pi-cli/`，不碰用户全局 |

### 4.3 分层与模块

| 层 | 职责 | 位置 |
|----|------|------|
| 接口层 | HTTP、校验、CORS、OpenAPI | `src/digital_marketing/api/` |
| 领域内核 | 清洗、特征、训练、解释、分群、规则、模拟 | `data/ features/ models/ explain/ segment/ rules/ simulate/` |
| Agent | 工具、runtime、grounding、审计、skills、报告 | `agent/` |
| 基础设施 | 配置、路径、种子、日志、IO | `core/` |
| 表现层 | SPA | `frontend/`（约束见 DESIGN） |

**依赖规则：**

| 模块 | 可依赖 | 禁止 |
|------|--------|------|
| `data` | core | fastapi、frontend |
| `features` | data, core | 划分前 fit 全量 |
| `models` | features, core | 用 test 调参 |
| `explain` | models 产物 | 编造 shap |
| `segment` | features（无标签拟合） | 用 Conversion 训练簇 |
| `rules` | 分箱特征 | 宣称因果 |
| `simulate` | models 产物 + test 集 | 宣称因果收益、训练期使用 |
| `agent.tools` | 内核门面/产物只读 | 任意 shell |
| `agent.pi_runtime` | 仅 tools/pi-cli 可执行文件 | `which pi` / PATH 回退 |
| `api` | 各服务门面 | 内嵌超长训练循环 |

### 4.4 目标包结构

```text
src/digital_marketing/
  core/
  data/          # load, clean, quality, split
  features/
  models/        # classify, imbalance, metrics, calibrate, ensemble
  explain/       # shap, pdp, counterfactual
  segment/       # cluster, compare
  rules/
  simulate/      # budget（期望值口径）
  agent/
    config.py    # Stage 1：agent.yaml 统一加载（缓存 + pydantic 校验）
    tools/       # __init__ 装饰器注册中心 + catalog 实现 + facts 抽取器
    prompts/
    skills/      # 项目内 Pi --skill（7 个 SKILL.md）
    local_runtime.py
    pi_runtime.py
    grounding.py # 五段契约 + facts_from_tool 分派壳
    audit.py
    report.py
    service.py   # runtime 分发（pi → run_pi_chat / 其余 → local）
  api/
    main.py
    deps.py
    routes_*.py
  schemas/       # pydantic DTO
```

### 4.5 数据流（双轨）

```text
raw CSV (data/, 只读真相源)
  │
  ├─【主数据轨】import → outputs/db/app.db (campaigns + import_batches)
  │              API 列表/按 CustomerID 查询；可随时删库重建
  │
  └─【产物轨】load → quality profile → docs/reports + outputs/
                 → clean → outputs/processed/
                 → stratified split → splits 元数据
                 → fit features on train → feature_schema.json
                 → train → outputs/models/<run_id>/
                 → metrics / figures / shap（文件，不进 SQLite）
                 → segment / rules artifacts
                 → API 只读加载 artifact
                 → Agent 工具只读调用门面或产物
```

**禁止：**

- 把 `app.db` 放在 `data/`  
- 覆盖 `data/` 原始 CSV  
- 把 metrics / model blob / SHAP 矩阵塞进 SQLite（本仓库产物轨固定为文件）

**产物目录：** `config/settings.yaml` 固定 `outputs/`（含 `outputs/db/app.db`）。

| 产物 | 用途 |
|------|------|
| `outputs/db/app.db` | **主数据轨**：营销活动行（可重建） |
| `outputs/models/<run_id>/model.*` | 推理 |
| `outputs/models/<run_id>/transformer.joblib` | per-run 特征管道（E5/E6/E7 等变体 run；缺省回退全局） |
| `outputs/models/<run_id>/metrics.json` | 评估/论文/前端（含 cv/ci/pr_curve/roc_curve/lift_deciles/threshold_scan） |
| `outputs/models/<run_id>/feature_schema.json` | 推理校验 |
| `outputs/models/<run_id>/config_snapshot.yaml` | 复现 |
| `outputs/metrics/leaderboard.json` | 实验矩阵对比（E0–E8） |
| `outputs/metrics/calibration_<run_id>.json` | E8 校准前后对比 |
| `outputs/explain/pdp_<run_id>.json` | PDP/ICE 网格（Top 特征） |
| `outputs/segments/summary.json` | 分群 |
| `outputs/segments/compare.json` | 多算法分群对比 + 稳定性 + PCA 投影 + 自动画像名 |
| `outputs/simulate/budget_curve_<run_id>.json` | 预算模拟默认参数曲线 |
| `outputs/simulate/reach_list_<run_id>.csv` | Top-K 触达名单 |
| `outputs/rules/top_rules.json` | 规则 |
| `outputs/reports/analysis_*.md` | Agent 一键分析报告 |
| `outputs/agent_logs/*.jsonl` | 审计 |
| `outputs/agent_sessions/` | Pi/会话 |

---

## 5. 仓库结构约束

### 5.1 根目录允许

`README.md`、`LICENSE`、`.gitignore`、`AGENTS.md`、`DESIGN.md`、`CHANGE.md`、`requirements.txt`/`pyproject.toml`、`.env.example`；可选 `docker-compose.yml`、`Makefile`。

### 5.2 标准目录

```text
data/                  # 原始只读 CSV（真相源）
config/
src/digital_marketing/
frontend/              # UI，详见 DESIGN.md
scripts/               # init_db / import_campaigns / 后续 run_all 等
tools/pi-cli/          # 项目内 Pi
tests/
notebooks/             # 探索用；结论必须回流 src/
docs/plans/
docs/reports/
outputs/               # gitignore 大文件与 *.db
outputs/db/            # SQLite app.db（主数据轨，可重建）
```

| 类型 | 目录 |
|------|------|
| 计划 | `docs/plans/` |
| 报告 | `docs/reports/` |
| 配置 | `config/` |
| 脚本 | `scripts/` |
| 测试 | `tests/` |
| 前端 | `frontend/` |
| 后端源码 | `src/digital_marketing/` |

---

## 6. 语言与代码风格（全栈）

| 场景 | 要求 |
|------|------|
| 文档、CHANGE、报告、UI 文案 | 中文 |
| 注释、docstring | 中文 |
| 标识符、API 路径、配置键 | 英文 |
| commit | `type(scope):中文总结` |

**Python：** 3.11+；包名 `digital_marketing`；公开 API 尽量类型标注；`random_seed` 统一配置（默认 42）；避免硬编码用户机器绝对路径。  

**前端栈锁定：** Vue 3 + Vite + Element Plus + ECharts + axios（细则与视觉见 `DESIGN.md`）。  

**复用：** 改前先搜；第三次重复再抽取；notebook 逻辑必须进 `src/` 再给 API。  

---

## 7. 数据与特征

1. 原始：`data/digital_marketing_campaign_dataset.csv` 只读真相源。  
2. **主数据轨：** CSV → `python scripts/import_campaigns.py` → `outputs/db/app.db`（`campaigns` / `import_batches`）；默认全量重建；`CustomerID` **可存可查、永不入模**。  
3. **丢弃入模：** `CustomerID`、`AdvertisingPlatform`、`AdvertisingTool`（常数广告字段可入库展示）。  
4. **质量须审计：** `EmailClicks > EmailOpens`；`WebsiteVisits==0` 仍有深度指标。主策略：保留 + flag（`email_inconsistent`、`invalid_web_metrics_flag`）；变更须报告 + CHANGE。  
5. **ConversionRate：** 入库；主模型默认不含；E5 消融。  
6. **划分：** 分层；先 split 后 fit；SMOTE/scaler/encoder 仅 train。  
7. 导出 `feature_schema.json`；推理校验字段。  
8. 展示数字优先来自 metrics 产物，禁止前端/Agent 口算写死。

**字段角色摘要：**

| 字段 | 入模默认 |
|------|----------|
| Age, Gender, Income | 是 |
| CampaignChannel, CampaignType | 是 |
| AdSpend, ClickThroughRate | 是 |
| ConversionRate | **否**（E5 可开） |
| 站内/邮件/社交/历史购买/积分 | 是 |
| Conversion | 仅标签 y |

---

## 8. 模型与指标

### 8.1 任务

主：二分类转化预测。辅：SHAP、分群、关联规则。

### 8.2 实验矩阵

| ID | 内容 | 备注 |
|----|------|------|
| E0 | Dummy 多数类 | 对照基线 |
| E1 | Logistic + class_weight | |
| E2 | RF / LightGBM 默认（无 class_weight） | 当前默认 run 出自此类 |
| E3 | 树模型 + 不平衡权重（主候选） | |
| E4 | E3 + SMOTE（仅 train；imblearn 缺失则跳过并声明） | |
| E5 | E3 + ConversionRate（泄漏消融） | **永不参选默认 run** |
| E6 | E3 − 质量 flag（消融） | **永不参选默认 run** |
| E7 | Stacking：LGBM+RF+LR → meta LR（train 5-fold OOF） | 解释降级为 permutation |
| E8 | E3 + 概率校准（Platt/Isotonic valid 择优） | 校准器仅 valid fit |

训练入口：`scripts/02_train_classify.py` 只跑基础实验；`scripts/06_train_full.py` 跑全矩阵。  
**默认 run 保护：** `services/artifacts.pick_default_run_id` 排除 Dummy 与消融 run（meta.feature_schema 含 ConversionRate 或 ablation 标记），0.01 窗口近并列偏好纯树模型（stacking 不享树加成）。  
**per-run transformer：** 特征变体 run 目录存 `transformer.joblib`，`load_runtime` 优先读取，回退全局 processed。

### 8.3 主指标顺序

1. **PR-AUC**（test bootstrap 1000 次 95% CI；train 5-fold CV 均值±std）  
2. **ROC-AUC**  
3. F1 / 阈值后 Precision·Recall  
4. 混淆矩阵  
5. Accuracy 仅对照（须并列 Dummy）  

阈值：valid 搜索 → test **一次**评估。LightGBM 优先，装不上则 RF。

**增强评估（每 run 落盘）：** `pr_curve`/`roc_curve`（≤200 点抽稀）、`lift_deciles`（十分位 capture/lift）、`threshold_scan`（期望成本 = FP×1 + FN×5，可配）、E8 另落 `calibration_<run_id>.json`（brier/log_loss/ECE 前后对比）。**CI 重叠的 run 之间不得宣称「更优」。**

### 8.4 SHAP / 分群 / 规则 / PDP / 反事实 / 模拟

- SHAP：TreeExplainer 优先（stacking 回退 permutation 并标注 method）；全局 Top-K + 局部列表；文案不说「必然导致」。  
- PDP/ICE：主 run Top 特征网格（`explain/pdp.py`），原始特征空间扰动。  
- 反事实（`explain/counterfactual.py`）：单特征扰动曲线 + 贪心最小改动路径；**仅描述模型行为（敏感性分析），强制 disclaimer，不构成因果效应或投放建议**。  
- 分群：K-Means 主；**训练不含 Conversion**；事后画像转化率。多算法对比（KMeans/GMM/Agglomerative × K）+ bootstrap ARI 稳定性 + PCA 投影 + 规则化自动画像名（z-score Top2，无 LLM）。  
- 规则：分箱 + mlxtend；support/confidence/lift；声明相关非因果。  
- 预算模拟（`simulate/budget.py`）：test 集 proba × 单客价值 − 触达成本 → 期望价值排序 + K 扫描；**期望值口径，非因果收益承诺**。  

---

## 9. Agent 与项目内 Pi

### 9.1 原则

- **Host-executed tools：** 工具在本仓库 Python 执行；LLM/Pi 只编排与叙述。  
- 默认 runtime：**`pi`**（编排中枢）；stub/未安装/失败时**明确降级 local 并在响应 `pi_fallback` 与 `open_questions` 标注**；无 Key 可 `template`。  
- 输出字段：`observed_facts` / `inferences` / `recommendations` / `open_questions` / `tool_trace`。  
- skills 生态：`agent/skills/<name>/SKILL.md` ×7（frontmatter name/description + 编排步骤 + 口径红线）；模板模式复用同套编排，保证无 Key 可演示。  
- 一键报告：`generate_analysis_report` 编排工具 → markdown 落盘 `outputs/reports/analysis_<ts>.md`，数字全部来自工具结果，尾部固定「口径与限制」节。
- **图表工具（Stage4）：** `render_chart` 由宿主从真实数据源（SQLite/产物）计算数据 → 返回 chart-spec v1.0 纯 JSON；前端 `ChartCard` 映射渲染，**色板以前端 tokens 为唯一真相**；LLM/Pi 永不产数字、**永不产 spec**（Pi 集成层输出仅叙述文本）。  

### 9.2 工具注册表

| 工具 | 阶段 |
|------|------|
| `get_dataset_profile` | P0 |
| `get_data_quality_issues` | P0 |
| `conversion_by_dimension` | P0 |
| `get_model_metrics` | P0 |
| `get_feature_schema` | P0 |
| `predict_proba` | P0 |
| `explain_global` / `explain_customer` | P0 |
| `segment_summary` / `assign_cluster` | P1 |
| `top_association_rules` / `strategy_brief` | P1 |
| `compare_experiments` | 阶段9 |
| `get_calibration_summary` | 阶段9 |
| `get_lift_table` | 阶段9 |
| `simulate_budget` | 阶段9 |
| `counterfactual_explain` | 阶段9 |
| `generate_analysis_report` | 阶段9 |
| `render_chart`（声明式图表 spec，9 数据集 × 6 图型） | Stage4 |

新增工具（Stage 1 起）：**一处定义**——`tools/catalog.py` 用 `@tool(name, keywords=..., base_kwargs=..., plan=..., facts=..., plan_order=..., stage=...)` 装饰器声明，REGISTRY 注册、`plan_from_message` 关键词路由、grounding 事实分派（`tools/facts.py`）自动生效；再更新本节表格 + `agent.yaml` `tools.whitelist`（非空时 run_tool 校验交集）+ 单测 + CHANGE。旧入口 `plan_tools`/`facts_from_tool`/`try_pi_or_fallback` 为兼容别名。

### 9.3 项目内 Pi CLI

| 规则 | 要求 |
|------|------|
| 目录 | 仅 `tools/pi-cli/` |
| 安装 | `python scripts/setup_pi_cli.py` |
| 版本 | package.json / lock / VERSION |
| 可执行文件 | `config/agent.yaml` → `pi.executable`，路径必须在 `tools/pi-cli/` 下 |
| PATH | **禁止** `which pi`、禁止全局回退 |
| 作用域 | **仅本仓库本地** |
| 会话 | `outputs/agent_sessions/` |
| 未安装 | 明确错误 + 降级 local |
| 测试 | 断言 executable 前缀合法 |

```text
setup_pi_cli.py
  → npm install --prefix tools/pi-cli 锁定 @earendil-works/pi-coding-agent
  → 写入 VERSION / lock
  → 解析 bin 写入 pi.executable（相对项目根）

PiRuntime.run()
  → assert path 位于 project_root/tools/pi-cli
  → cwd=project_root；超时与输出上限
  → 解析为统一 AgentResult
```

### 9.4 审计 jsonl（每行）

`ts, request_id, session_id, runtime, user_message, tool_calls, reply_digest, latency_ms, error`

### 9.5 密钥

仅环境变量 / 本地 `.env`（gitignore）；仓库只留 `.env.example`。

---

## 10. API 设计（后端契约）

### 10.1 约定

- 前缀：`/api/v1`  
- Envelope：

```json
{ "ok": true, "data": {}, "error": null, "request_id": "uuid" }
```

```json
{
  "ok": false,
  "data": null,
  "error": { "code": "MODEL_NOT_LOADED", "message": "中文说明", "detail": {} },
  "request_id": "uuid"
}
```

### 10.2 端点

| 方法 | 路径 | 阶段 |
|------|------|------|
| GET | `/health` | P0 |
| GET | `/data/overview` | P0 |
| GET | `/data/dashboard` | Stage3（大屏聚合：KPI/伪漏斗/直方图 + caliber 口径字段） |
| GET | `/data/cross-matrix` | Stage3（二维交叉转化率矩阵；维度白名单 channel/type/gender） |
| GET | `/meta/features` | P0 |
| GET | `/models/metrics` | P0 |
| GET | `/models/metrics/{run_id}` | P0 |
| POST | `/models/predict` | P0 |
| POST | `/models/predict/batch` | P1（条数上限 200） |
| GET | `/models/curves` | 阶段9（pr/roc 点 + CI） |
| GET | `/models/calibration` | 阶段9（E8 校准前后对比） |
| GET | `/models/lift` | 阶段9（十分位 lift 表） |
| GET | `/models/threshold-scan` | 阶段9（成本敏感阈值扫描） |
| GET | `/explain/global` | P0 |
| POST | `/explain/customer` | P0 |
| GET | `/explain/pdp` | 阶段9（PDP/ICE 网格） |
| POST | `/explain/counterfactual` | 阶段9（模型行为口径，强制 disclaimer） |
| GET | `/segments` | P1 |
| POST | `/segments/assign` | P1 |
| GET | `/segments/compare` | 阶段9（多算法对比 + 稳定性 + 自动画像名） |
| GET | `/segments/projection` | 阶段9（PCA 2D 投影） |
| GET | `/rules` | P1 |
| POST | `/simulate/budget` | 阶段9（期望值口径，`export=true` 落 CSV） |
| POST | `/agent/chat` | P0 |
| GET | `/agent/sessions/{session_id}` | P0 |
| POST | `/agent/runtime` | P1 |
| GET | `/agent/pi/status` | P1（含 is_stub/default_runtime/skills/fallback_reason） |
| GET | `/agent/audit/recent` | 阶段9（审计行倒序，limit 1–500） |
| POST | `/agent/report` | 阶段9（一键分析报告落盘） |

### 10.3 关键响应字段

- **预测：** `proba`, `label`, `threshold`, `run_id`, `model_name`  
- **解释：** `top_features[{name, feature_value, shap_value}]`, `method`, `run_id`  
- **Agent：** 五段字段 + `tool_trace` + `session_id` + `runtime` + `pi_fallback`（Pi 降级标注）  
- **模拟：** `curve[{k, expected_net, ...}]` + `recommended_k` + `top_list`（≤50 预览）+ `disclaimer`
- **chart-spec v1.0（Stage4 `render_chart`）：** `{spec_version, chart_type(bar|line|pie|scatter|heatmap|funnel), title, categories[], series[{name,values[]}], value_format(int|float4|percent2|money), axis{x_name,y_name}, caliber, source{kind,ref,run_id}, disclaimer?}`；数据集白名单 9 项（conversion_by_channel/type、leaderboard_pr、age/income/adspend_hist、segment_sizes、lift_deciles、global_shap_top）；越界 `VALIDATION_ERROR`
- **大屏聚合（Stage3 描述性口径，后端为真相源）：**
  - 伪漏斗四阶段（`services/dashboard.py::FUNNEL_STAGES`）：`clicked`(email_clicks>0 OR click_through_rate>0) → `visited`(website_visits>0) → `deep_visited`(visited AND pages_per_visit≥2) → `converted`(conversion=1)
  - **横截面独立计数、非 cohort、阶段不嵌套**（阶段间差异不构成流失率/环比）；原始数据无业务时间字段，**时序永不可做**
  - `caliber` 字段前端必须原样展示，禁止前端自造口径文案  

### 10.4 错误码示例

`VALIDATION_ERROR` / `SCHEMA_MISMATCH` / `MODEL_NOT_LOADED` / `ARTIFACT_MISSING` / `AGENT_TOOL_FAILED` / `PI_NOT_INSTALLED` / `PI_PATH_INVALID` / `LLM_UNAVAILABLE` / `RATE_LIMIT`

### 10.5 CORS 与安全默认

- 开发：允许 Vite 源  
- 不要默认无说明的 `allow_origins=["*"]` 当生产配置  
- 默认**无登录**（本地答辩）；公网暴露须另开设计并记 CHANGE  

---

## 11. 配置

| 文件 | 内容 |
|------|------|
| `config/settings.yaml` | 路径、`database.path`、API CORS、seed、日志 |
| `config/features.yaml` | 丢弃列、可选列、分箱（后续） |
| `config/model.yaml` | 超参、阈值目标（后续） |
| `config/agent.yaml` | runtime、LLM、pi.executable、工具开关、审计路径（后续） |

**`settings.yaml` 关键：**

- `paths.raw_csv` / `paths.outputs_dir` / `paths.db_dir`  
- `database.path`：默认 `outputs/db/app.db`（相对项目根）  
- `api.prefix`：`/api/v1`；`api.cors_origins`：Vite 开发源  

**环境变量：** `DIGITAL_ROOT` / `DIGITAL_DATABASE_URL` / `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `DIGITAL_AGENT_RUNTIME`

**agent.yaml 示意：**

```yaml
runtime: pi            # 默认编排中枢；stub/未安装明确降级 local 并标注
llm:
  provider: deepseek
  model: deepseek-chat
  base_url: https://api.deepseek.com
  timeout_sec: 60
pi:
  executable: tools/pi-cli/node_modules/.bin/pi
  skills_dir: agent/skills
  session_dir: outputs/agent_sessions
  timeout_sec: 180
tools:
  whitelist: []        # 与工具注册表同步（五处联动）
audit:
  log_dir: outputs/agent_logs
  session_dir: outputs/agent_sessions
```

`pi.executable` **禁止**配置成无路径的裸 `pi`。

---

## 12. 安全

| 风险 | 控制 |
|------|------|
| 密钥泄露 | env + gitignore；日志脱敏 |
| 任意命令 | 无通用 shell 工具；Pi 默认走 host tools |
| 路径穿越 | IO 限制在项目根子目录 |
| 批量滥用 | batch 上限 |
| 全局 Pi | 路径前缀校验 + 测试 |
| 原始数据 | 不覆盖 raw |

---

## 13. 测试与完成定义

| 改动 | 最低验证 |
|------|----------|
| 清洗 | 单测 + 质量计数 |
| 训练 | scripts 通 + metrics 落盘 |
| API | 路由测试或手工命中 |
| Agent | 工具单测 + tool_trace |
| Pi | status 路径在 tools/pi-cli |
| 前端 | 见 DESIGN 检查清单 + 关键路径手点 |

禁止虚假完成：测试失败不称完成；跳过步骤须声明。

**复现命令（P0/P1/阶段9 主线）：**

```text
pip install -e ".[dev]"
# 可选 SMOTE 等：pip install -e ".[dev,ml]"
python scripts/init_db.py
python scripts/import_campaigns.py
python scripts/run_all.py
python scripts/run_all.py --with-p1            # 分群 + 规则
python scripts/run_all.py --with-p1 --full     # 全量矩阵 E0–E8 + PDP + 预算模拟 + 分群对比
python scripts/setup_pi_cli.py                 # 可选，仅 tools/pi-cli/
python scripts/export_paper_tables.py          # 论文表（CV/CI/Brier 列）
pytest
uvicorn digital_marketing.api.main:app --reload --port 9800
cd frontend && npm install && npm run dev
# 前端开发端口 5600；API baseURL → http://127.0.0.1:9800/api/v1
```

**实现状态摘要：** 清洗/训练 E0–E8 全矩阵（Stacking/校准/消融）/SHAP/PDP/反事实/多算法分群/预算模拟/全量 API（含模拟与报告 + Stage3 描述性聚合 dashboard/cross-matrix）/十路由前端（+/screen 大屏，四层叙事分组）/Agent 装饰器工具注册 + render_chart 图表工具（chart-spec v1.0 会话内联渲染）/Pi 编排中枢（默认 runtime + 7 skills + 一键报告 + 审计回放；真实编排协议已侦察锁定，待真实安装落实）已落地。开发端口：API **9800**、前端 **5600**。P2（RAG、K8s、多租户、因果 uplift 主线）默认不做。

---

## 14. Git 与 CHANGE

**Commit（用户要求时）：** `type(scope):中文总结`  
type：feat/fix/docs/refactor/test/chore/perf/style；scope 为 kebab-case。

**CHANGE.md：** 每次有意义修改在**顶部**追加（模板见 CHANGE 文首）。  
有意义：功能/修复/约束/API/指标口径/依赖大版本/安全。  
纯空格格式化可省略，仍鼓励 docs 一条。

---

## 15. AI 代理工作方式

1. 先读后改；禁止未读整文件覆盖。  
2. 最小 diff；禁止无关重构搭车。  
3. 不擅自开 P2；不引入 RAG/K8s/新框架。  
4. 架构/后端变更 → 本文件；UI 变更 → DESIGN；都记 CHANGE。  
5. 中文沟通；标识符英文。  
6. Pi 只用项目内；误用全局视为缺陷。  
7. 不破坏性删数据；不泄密钥。  
8. 诚实报告失败与未验证项。  

---

## 16. 决策变更流程

打破硬约束：

1. 用户确认  
2. 改 `AGENTS.md` 和/或 `DESIGN.md`  
3. 记 `CHANGE.md`  
4. 影响范围则改 `docs/plans/`  
5. 再改代码  

---

## 17. ADR 摘要（架构决策）

| 决策 | 选择 | 理由 |
|------|------|------|
| 后端 | FastAPI | 轻量、OpenAPI、毕设友好 |
| 前端 | Vue3+Element Plus | 见 DESIGN；交付快 |
| **营销主数据** | **SQLite `outputs/db/app.db`** | 8k 行可重建缓存；查询/按 ID；CSV 仍为真相源 |
| **分析产物** | **`outputs/` 文件** | 模型/metrics/SHAP/分群/规则/审计；不进 SQLite |
| ORM | SQLAlchemy 2.0 + 同步 sqlite3 | 导入/脚本同步；本阶段不做 aiosqlite/Alembic |
| 主模型 | LightGBM（后备 RF） | 表格+SHAP |
| 主指标 | PR-AUC | 严重不平衡 |
| Agent | 工具接地 + 可插拔 Runtime | 避免贴皮 |
| Pi | tools/pi-cli 项目内；**默认 runtime=pi（编排中枢）** | 可复现、不污染用户环境；stub/未安装明确降级并标注 |
| 默认 run 保护 | 消融/泄漏 run（E5/E6）不参选默认 | 防泄漏结论被误当主结论 |
| 登录 | 默认无 | 控范围 |
| ConversionRate | 默认不入模 | 降泄漏质疑 |

**落选：** 仅 Jupyter；强绑 LangChain 全家桶；全局 Pi；以 Accuracy 优化；metrics 进 SQLite；`app.db` 放 `data/`。

---

## 18. 会话结束检查清单

```text
□ 目录归位正确？
□ 未覆盖 data/ 原始 CSV？app.db 不在 data/？
□ metrics/模型未误写入 SQLite？
□ 未违反指标/泄漏/ID 规则？
□ Pi 仍只指向 tools/pi-cli？
□ Agent 数字可追溯？
□ 架构/API 变更已写本文件？
□ UI 变更已写 DESIGN？
□ 已追加 CHANGE.md？
□ 无密钥入库？
□ 验证已做或已声明未做？
```

---

## 19. 与通用技能的关系

遵守用户环境通用技能（中文优先、目录规范、commit 格式等）。**本仓库特有**的 Pi 隔离、指标纪律、文档分工以本文件 + DESIGN 为准。

---

**维护：** 代码落地后路径与真实实现对齐时，升版本文并记 CHANGE「路径对齐」。前端一切观感与页面规范不在此展开 → 见 `DESIGN.md`。
