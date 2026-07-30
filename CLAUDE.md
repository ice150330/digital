# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目状态（2026-07-30）

本科毕设仓库：**数字营销转化分析 + 工具接地 AI Copilot**。当前几乎无业务代码——已有治理文档、计划、原始数据与 Pencil 组件库；`src/`、`frontend/`、`scripts/`、`config/`、`tests/` 待按计划落地。

权威约束不在本文件重复展开：

| 文档 | 职责 |
|------|------|
| **`AGENTS.md`** | 开发/代理行为、架构、数据/ML、API、Agent/Pi、配置、安全、测试（**先读**） |
| **`DESIGN.md`** | 仅前端：路由、布局、token、组件、图表、接口消费 |
| **`docs/plans/`** | 范围、P0/P1/P2、24 周里程碑 |
| **`CHANGE.md`** | 有意义改动人工记录（最新在上） |
| **`pen/ui.pen`** | 组件参考库（设计资源，非整页） |

冲突优先级：硬禁止以 `AGENTS.md` 为准；UI 以 `DESIGN.md` 为准；范围以计划书为准。

## 常用命令（目标形态）

实现就绪后的复现路径（见 AGENTS §13）：

```bash
# 后端依赖
pip install -r requirements.txt

# 训练/清洗/指标一键产物 → outputs/
python scripts/run_all.py

# 可选：项目内 Pi CLI（禁止用用户全局 pi）
python scripts/setup_pi_cli.py

# API
uvicorn src.digital_marketing.api.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev

# 测试
pytest
pytest tests/path/to/test_file.py          # 单文件
pytest tests/path/to/test_file.py::test_x  # 单用例
```

前端包管理在项目内锁定 **npm 或 pnpm 其一**；lockfile 入库。LLM Key 仅环境变量 / 本地 `.env`（gitignore），仓库只留 `.env.example`。

## 架构总览

```text
Vue SPA (frontend/)  ──REST /api/v1/*──►  FastAPI (src/digital_marketing/api/)
                                              │
                         ┌────────────────────┼────────────────────┐
                         ▼                    ▼                    ▼
                  Analysis Core          Agent Service         文件系统
               clean/features/train    tools + local|pi      outputs/
               shap/segment/rules      audit jsonl           config/
                                              │
                                              ▼
                                    tools/pi-cli/（可选，项目内）
```

- **内核与 Agent 分离**：指标与模型只来自分析产物；Agent 工具只读门面/产物，不编造数字。
- **产物驱动**：论文表、API、前端、Agent 共用 `outputs/`（如 `models/<run_id>/metrics.json`）。
- **包名**：`digital_marketing`，代码在 `src/digital_marketing/`。
- **依赖方向**：`data` → `features` → `models` → `explain`；`segment` 训练不含标签；`api` 调服务门面，不内嵌超长训练；`pi_runtime` 禁止 PATH/`which pi` 回退。

目标目录（未建齐时按此创建，勿堆根目录）：

```text
data/  config/  src/digital_marketing/  frontend/  scripts/
tools/pi-cli/  tests/  notebooks/  docs/plans/  docs/reports/  outputs/  pen/
```

根目录允许：`README`/`LICENSE`/`.gitignore`/`AGENTS`/`DESIGN`/`CHANGE`/`CLAUDE`/`requirements|pyproject`/`.env.example` 等。计划与报告进 `docs/`，脚本进 `scripts/`。

## 数据与 ML 红线

- 源数据：`data/digital_marketing_campaign_dataset.csv`（约 8000×20，目标 `Conversion` ~87.65% 正类）**只读**；清洗写 `outputs/processed/`。
- **永不入模**：`CustomerID`。常数广告字段丢弃。`ConversionRate` 主模型默认不含（E5 消融才对比）。
- **先 split 后 fit**；imputer/scaler/encoder/SMOTE 仅 train；阈值在 valid 搜、test 一次评估。
- **主指标顺序**：PR-AUC → ROC-AUC → F1/阈值后 PR → 混淆矩阵；Accuracy 仅对照并并列 Dummy。
- 分群训练不含 `Conversion`；关联规则声明相关非因果。

## API 与 Agent

- 前缀 `/api/v1`；统一 envelope：`{ ok, data, error, request_id }`。
- 预测须带回 `proba` / `label` / `threshold` / `run_id`；解释带回 `top_features` + `method`。
- Agent 输出契约：`observed_facts` / `inferences` / `recommendations` / `open_questions` / `tool_trace`。
- Runtime：默认 `local`；`pi` 仅 `tools/pi-cli/`（`config/agent.yaml` → `pi.executable`）；无 Key 可 `template`。
- 审计：`outputs/agent_logs/*.jsonl`；会话：`outputs/agent_sessions/`。

## 前端要点（细节见 DESIGN）

- 栈：**Vue 3 + Vite + Element Plus + ECharts + axios**（勿擅自换 React 等）。
- 路由：`/` 总览、`/models`、`/customers`、`/segments`、`/rules`、`/agent`、`/about`。
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

P0：数据清洗与质量报告、分类实验（含 Dummy）、SHAP、FastAPI 核心端点、Vue 总览/模型/客户/Agent、LocalToolRuntime。  
P1：分群、关联规则、项目内 Pi 插拔。  
永不砍：防泄漏叙述、PR-AUC 主指标、可运行 API、工具接地 Agent。
