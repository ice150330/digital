# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目状态（2026-07-30）

本科毕设仓库：**数字营销转化分析 + 工具接地 AI Copilot**。

**已落地：** M0 + 清洗/split + E0/E1/E3 + SHAP/P0 API + **前端七路由** + **Local Agent** + **分群/规则** + **batch** + **项目内 Pi** + **阶段8**（demo checklist / 论文表导出 / 测试补强）。  
**端口：** API **9800** · 前端 **5600**。  
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

# 分类实验 E0/E1/E3 → outputs/models|metrics
python scripts/02_train_classify.py

# 全局解释 + 样例缓存
python scripts/03_explain_shap.py

# 分群 / 关联规则（P1）
python scripts/04_train_cluster.py
python scripts/05_mine_rules.py

# 一键（清洗→训练→解释；可选 P1）
python scripts/run_all.py
python scripts/run_all.py --with-p1

# 项目内 Pi stub/安装（禁止全局 pi）
python scripts/setup_pi_cli.py

# 测试
pytest
pytest tests/test_api_core.py
pytest tests/test_agent_tools.py
pytest tests/test_segment_rules.py
pytest tests/test_pi_path.py

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
                tools/pi-cli/（可选，项目内）
```

- **双轨存储：** 营销行在 SQLite；模型/metrics/SHAP 等分析产物在 `outputs/` **文件**，**不进** SQLite。CSV 只读真相源。
- **内核与 Agent 分离**：指标与模型只来自分析产物；Agent 工具只读门面/产物，不编造数字。
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
  - `GET /models/metrics`、`GET /models/metrics/{run_id}`、`POST /models/predict`、`POST /models/predict/batch`
  - `GET /explain/global`、`POST /explain/customer`
  - `GET /segments`、`POST /segments/assign`、`GET /rules`
  - `POST /agent/chat`、`GET /agent/sessions/{id}`、`POST /agent/runtime`、`GET /agent/pi/status`
- 预测须带回 `proba` / `label` / `threshold` / `run_id`；解释带回 `top_features` + `method`。
- 默认 run：非 Dummy 中 PR-AUC 最高，近并列偏好树/LightGBM（解释友好）。
- Agent 输出契约：`observed_facts` / `inferences` / `recommendations` / `open_questions` / `tool_trace`。
- Runtime：默认 `local`；`pi` 仅 `tools/pi-cli/`（`config/agent.yaml` → `pi.executable`）；无 Key 可 `template`。
- 审计：`outputs/agent_logs/*.jsonl`；会话：`outputs/agent_sessions/`。

## 前端要点（细节见 DESIGN）

- 栈：**Vue 3 + Vite + Element Plus + ECharts + axios**（勿擅自换 React 等）。当前空壳已接 Element Plus + axios + vue-router；ECharts 待业务页。
- 路由：`/` `/models` `/customers` `/segments` `/rules` `/agent` `/about` 均已挂业务或真数据页。
- 数字一律来自后端；禁止前端假造 AUC。`baseURL` 用 `VITE_API_BASE_URL`。
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

P0/P1/阶段8 主线已齐；后续仅答辩彩排与文案微调。  
永不砍：防泄漏叙述、PR-AUC 主指标、可运行 API、工具接地 Agent、Pi 仅 `tools/pi-cli/`。
