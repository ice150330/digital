# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目状态（2026-07-31）

本科毕设仓库：**数字营销转化分析 + 工具接地 AI Copilot + Pi 真实编排中枢**。

**已落地：** M0 + 清洗/split + **E0–E8 全实验矩阵**（含 SMOTE/泄漏消融/Stacking/校准）+ CV/CI/曲线/lift/阈值扫描 + SHAP/PDP/反事实 + 多算法分群/PCA/稳定性 + 规则 + **预算模拟器** + 全量 API + **前端十路由**（+`/screen` 全屏大屏）+ **Pi 真实编排**（v0.83.0 SDK 桥接：`createAgentSession` + customTools 宿主代理，默认 runtime=pi、失败降级 local）。
**2026-07-31 重构：** `@tool` 装饰器一处注册、L1 描述性端点（dashboard/cross-matrix）、`render_chart` 图表工具（会话内联出图）、BaseChart 封装与色板单一真相、侧栏四层叙事分组、反事实/E4·E6 叙事降级（E5/E7/E8 主线保留）。  
**端口：** API **9800** · 前端 **5600**。  
**验证：** `pytest` 114 passed。  
**P2 默认不做。**

权威约束不在本文件重复展开：

| 文档 | 职责 |
|------|------|
| **`AGENTS.md`** | 开发/代理行为、架构、数据/ML、API、Agent/Pi、配置、安全、测试（**先读**） |
| **`DESIGN.md`** | 仅前端：路由、布局、token、组件、图表、接口消费 |
| **`docs/plans/`** | 范围、P0/P1/P2、24 周里程碑 |
| **`CHANGE.md`** | 有意义改动人工记录（最新在上） |
| **`pen/ui.pen`** | 组件参考库（设计资源，非整页） |

冲突优先级：硬禁止以 `AGENTS.md` 为准；UI 以 `DESIGN.md` 为准；范围以计划书为准。

## 常用命令

```bash
# 后端依赖（可编辑安装）
pip install -e ".[dev]"

# SQLite 主数据轨
python scripts/init_db.py
python scripts/import_campaigns.py          # 默认 force 全量重建

# 清洗 + 分层 split + 质量报告
python scripts/01_clean_data.py
python scripts/00_profile_data.py --from-clean --write-report

# 分类实验：基础（E0/E1/E3）→ outputs/models|metrics
python scripts/02_train_classify.py

# 全量矩阵 E0–E8（消融/Stacking/校准 + CV/CI/曲线/lift/阈值扫描）
python scripts/06_train_full.py

# 全局解释 + 样例缓存
python scripts/03_explain_shap.py

# PDP/ICE + 预算模拟 + 分群对比
python scripts/07_explain_advanced.py
python scripts/08_simulate_budget.py
python scripts/09_cluster_compare.py

# 分群 / 关联规则（P1）
python scripts/04_train_cluster.py
python scripts/05_mine_rules.py

# 一键（清洗→训练→解释；可选 P1 / 全量）
python scripts/run_all.py
python scripts/run_all.py --with-p1
python scripts/run_all.py --with-p1 --full

# 项目内 Pi SDK 安装（@earendil-works/pi-coding-agent + typebox；禁止全局 pi）
python scripts/setup_pi_cli.py
# Pi 编排可选 env：DEEPSEEK_API_KEY（LLM 凭证）、PI_BRIDGE_MODEL（默认 deepseek/deepseek-chat）

# 测试
pytest
pytest tests/test_api_core.py
pytest tests/test_agent_tools.py
pytest tests/test_agent_config.py
pytest tests/test_api_dashboard.py
pytest tests/test_segment_rules.py
pytest tests/test_pi_path.py
pytest tests/test_pi_bridge.py
pytest tests/test_train_full.py
pytest tests/test_simulate.py
pytest tests/test_counterfactual.py
pytest tests/test_api_advanced.py
pytest tests/test_agent_runtime.py

# 论文表导出 / 演示清单
python scripts/export_paper_tables.py
# 见 scripts/demo_checklist.md

# API（包入口，非 src. 前缀）— 端口 9800
uvicorn digital_marketing.api.main:app --reload --port 9800

# 前端 — 端口 5600
cd frontend && npm install && npm run dev
cd frontend && npm run build
```

前端包管理锁定 **npm**（`frontend/package-lock.json`）。LLM Key 仅环境变量 / 本地 `.env`（gitignore），仓库只留 `.env.example`。

## 架构总览

```text
Vue SPA (frontend/)  ──REST /api/v1/*──►  FastAPI (src/digital_marketing/api/)
                                              │
               ┌──────────────────────────────┼──────────────────────────┐
               ▼                    ▼         ▼                          ▼
        Analysis Core        Agent Service  SQLite 主数据轨         产物文件轨
     clean/features/train   tools+local|pi  outputs/db/app.db       outputs/{models,
     shap/segment/rules     audit           ← CSV 导入可重建         metrics,...}
               │                    │
               └──────────┬─────────┘
                          ▼
        tools/pi-cli/（Pi SDK 桥接：bridge/chat.mjs ↔ loopback /agent/tool-run）
```

- **双轨存储：** 营销行在 SQLite；模型/metrics/SHAP 等分析产物在 `outputs/` **文件**，**不进** SQLite。CSV 只读真相源。
- **内核与 Agent 分离**：指标与模型只来自分析产物；Agent 工具只读门面/产物，不编造数字。
- **Pi 宿主接地**：Pi（同进程 SDK）经 customTools 代理 HTTP loopback 回宿主 `POST /agent/tool-run` 实算；`noTools:'builtin'` 禁内置文件/shell 工具；工具清单来自 `GET /agent/tools/manifest`（@tool 声明为唯一真相）。
- **包名**：`digital_marketing`，代码在 `src/digital_marketing/`。
- **依赖方向**：`data` → `features` → `models` → `explain`；`segment` 训练不含标签；`api` 调服务门面；`pi_runtime` 禁止 PATH/`which pi` 回退。

目录：

```text
data/  config/  src/digital_marketing/  frontend/  scripts/
tools/pi-cli/  tests/  notebooks/  docs/plans/  docs/reports/  outputs/db/  pen/
```

根目录允许：`README`/`LICENSE`/`.gitignore`/`AGENTS`/`DESIGN`/`CHANGE`/`CLAUDE`/`requirements|pyproject`/`.env.example` 等。计划与报告进 `docs/`，脚本进 `scripts/`。

## 数据与 ML 红线

- 源数据：`data/digital_marketing_campaign_dataset.csv`（约 8000×20，目标 `Conversion` ~87.65% 正类）**只读**；清洗写 `outputs/processed/`；主数据导入 `outputs/db/app.db`。
- **永不入模**：`CustomerID`（可入库查询）。常数广告字段丢弃入模。`ConversionRate` 主模型默认不含（E5 消融才对比）。
- **先 split 后 fit**；imputer/scaler/encoder/SMOTE 仅 train；阈值在 valid 搜、test 一次评估。
- **主指标顺序**：PR-AUC → ROC-AUC → F1/阈值后 PR → 混淆矩阵；Accuracy 仅对照并并列 Dummy。
- 分群训练不含 `Conversion`；关联规则声明相关非因果。

## API 与 Agent

- 前缀 `/api/v1`；统一 envelope：`{ ok, data, error, request_id }`。
- **已实现：**
  - `GET /health`（`database_ok`、`campaigns_count`、`artifacts_ok`、`default_run_id`）
  - `GET /data/overview`、`GET /meta/features`
  - `GET /data/dashboard`（KPI/伪漏斗/直方图 + caliber 口径）、`GET /data/cross-matrix`（维度白名单）
  - `GET /models/metrics`、`GET /models/metrics/{run_id}`、`POST /models/predict`、`POST /models/predict/batch`
  - `GET /models/curves`、`GET /models/calibration`、`GET /models/lift`、`GET /models/threshold-scan`
  - `GET /explain/global`、`POST /explain/customer`、`GET /explain/pdp`、`POST /explain/counterfactual`
  - `GET /segments`、`POST /segments/assign`、`GET /segments/compare`、`GET /segments/projection`、`GET /rules`
  - `POST /simulate/budget`（期望值口径；`export=true` 落 CSV）
  - `POST /agent/chat`、`GET /agent/sessions/{id}`、`POST /agent/runtime`、`GET /agent/pi/status`
  - `GET /agent/tools/manifest`、`POST /agent/tool-run`（Pi 桥接：工具清单 + loopback 执行口）
  - `GET /agent/audit/recent`、`POST /agent/report`（一键分析报告 → `outputs/reports/`）
- 预测须带回 `proba` / `label` / `threshold` / `run_id`；解释带回 `top_features` + `method`。
- 默认 run：非 Dummy **非消融**中 PR-AUC 最高，0.01 窗口近并列偏好纯树/LightGBM（stacking 不享树加成；E5/E6 消融 run 代码级排除）。
- Agent 输出契约：`observed_facts` / `inferences` / `recommendations` / `open_questions` / `tool_trace`。
- Runtime：**默认 `pi`（真实编排中枢）**；桥接未就绪/失败明确降级 local 并在响应 `pi_fallback` + `open_questions` 标注；`pi` 仅 `tools/pi-cli/`（SDK 包 + `bridge/chat.mjs`）；无 Key 可 `template`。
- 工具注册：`@tool` 装饰器一处定义（catalog.py）；新增工具同步 `agent.yaml` whitelist + 本节 + CHANGE。
- 审计：`outputs/agent_logs/*.jsonl`；会话：`outputs/agent_sessions/`；skills：`agent/skills/*/SKILL.md` ×7。

## 前端要点（细节见 DESIGN）

- 栈：**Vue 3 + Vite + Element Plus + ECharts + axios**（勿擅自换 React 等）。ECharts 经 `utils/echarts.ts` 按需注册；所有图表经 `BaseChart` 渲染；图表色统一 `utils/chartTheme.ts`（与 tokens.css 单一真相）。
- 路由：`/screen`（大屏，`meta.fullscreen` 绕过布局）`/` `/models` `/customers` `/segments` `/rules` `/simulate` `/agent` `/pi` `/about` 十路由均已挂真数据页；侧栏五组四层叙事（总览大屏 → 描述性分析 → 预测建模 → 深度挖掘 → AI 与系统）。
- 数字一律来自后端；禁止前端假造 AUC。`baseURL` 用 `VITE_API_BASE_URL`。
- `/agent` 页对 `render_chart` 工具结果经 `ChartCard` 内联渲染 chart-spec。
- 组件视觉参考：`pen/ui.pen`（KpiCard、ShapBarChart、ToolTracePanel 等）。

## 改动纪律

1. 会话开工：读 `AGENTS.md` →（改 UI 再读 `DESIGN.md`）→ 最新计划 → `CHANGE.md` 近条 → 目标代码。
2. 有意义改动在 `CHANGE.md` **顶部**追加条目。
3. 用户未要求时不 `git commit` / `push` / 改 git config。
4. Commit 格式（用户要求提交时）：`type(scope):中文总结`。
5. 文档/注释/UI 文案中文；标识符与 API 路径英文。
6. 打破硬约束须用户确认 → 改 AGENTS/DESIGN → CHANGE → 再改代码。
7. 不扩大到 P2（RAG、K8s、多租户、因果 uplift 主线等）除非用户明确要求。

## 实现优先级提示

P0/P1/阶段8/阶段9 + 2026-07-31 重构计划（Stage 1–6）主线已齐；后续仅答辩彩排与文案微调。  
永不砍：防泄漏叙述、PR-AUC 主指标、可运行 API、工具接地 Agent（数字永不出宿主）、Pi 仅 `tools/pi-cli/`、E5/E6 消融不参选默认 run、反事实/模拟的「非因果」口径、伪漏斗横截面口径（时序永不做）。
