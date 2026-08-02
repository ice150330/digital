# digital

> 数字营销转化分析与 AI Copilot：一个面向本科毕业设计的可复现数据挖掘系统，覆盖营销转化预测、模型解释、分群规则、预算模拟，以及工具接地的 AI 分析台。

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

digital 不是一个简单的聊天壳，也不是只停留在 Notebook 的实验仓库。它把 `data/digital_marketing_campaign_dataset.csv` 中约 8000 条营销活动数据，组织成一条可复现的工程链路：

- 训练并比较 E0-E8 二分类实验矩阵，主指标使用 PR-AUC，而不是只看 Accuracy。
- 通过 SHAP/PDP/反事实敏感性分析解释模型行为，避免把相关性说成因果。
- 提供分群画像、关联规则、预算触达模拟和答辩可演示的可视化工作台。
- 内置 Agent/Pi 分析台：LLM 只负责编排和叙述，转化率、PR-AUC、图表数据全部由后端工具计算。

## 目录

- [功能亮点](#功能亮点)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [常用命令](#常用命令)
- [前端页面](#前端页面)
- [API 概览](#api-概览)
- [项目结构](#项目结构)
- [配置与安全](#配置与安全)
- [测试与验证](#测试与验证)
- [文档索引](#文档索引)

## 功能亮点

### 数据与模型

- **数据质量审计**：保留并标记邮件点击大于打开、访问为 0 但存在深度指标等异常，不覆盖原始 CSV。
- **泄漏防护**：`CustomerID` 永不入模，`ConversionRate` 默认不作为主模型特征，仅用于消融实验。
- **实验矩阵**：Dummy、Logistic、树模型、不平衡权重、SMOTE、泄漏消融、去质量 flag 消融、Stacking、概率校准。
- **主指标口径**：PR-AUC 优先，配合 ROC-AUC、F1、Precision/Recall、混淆矩阵、CV、Bootstrap 95% CI。
- **解释与模拟**：全局/局部解释、PDP/ICE、单客反事实敏感性、lift 十分位、成本敏感阈值扫描、预算触达模拟。

### Web 工作台

- **总览 Dashboard**：数据规模、正类占比、渠道表现、质量问题。
- **总览大屏 `/screen`**：浅色 AppLayout 内的中央渠道转化桑基图，外围小图串起转化、质量、划分和默认产物。
- **模型实验室**：E0-E8 对比、PR/ROC、校准、lift、阈值成本。
- **客户洞察**：单客预测、局部解释、反事实敏感性分析。
- **分群 / 规则 / 模拟**：分群画像、PCA 投影、关联规则、预算曲线和 Top 触达名单。
- **AI 分析台 `/agent`**：真实上游 LLM 流式回复、Markdown 消息、默认折叠的事实/推断/建议/待确认、内联 chart-spec 图表。
- **Pi 编排中枢 `/pi`**：PiAgent 配置卡片、Bridge Model 上游模型列表、健康检查、skills、审计日志、一键报告。

### Agent 与 Pi

- 默认 runtime 为 `pi`，未安装、stub 或桥接失败时明确降级到 `local` 并返回 `pi_fallback`。
- Pi 只允许使用项目内 `tools/pi-cli/`，禁止调用用户全局 `pi` 或修改用户 shell 配置。
- 工具清单来自后端 `@tool` 注册表；LLM/Pi 不产业务数字，不产 chart-spec。
- API Key 只读取环境变量或本地 `.env`，配置接口只返回掩码状态，不回显明文。

## 系统架构

```text
Vue 3 SPA (frontend, port 5600)
        │ HTTP JSON / SSE
        ▼
FastAPI (/api/v1, port 9800)
        │
        ├─ Analysis Core
        │  ├─ cleaning / split / feature build
        │  ├─ classification / calibration / metrics
        │  ├─ explain / segment / rules / simulate
        │  └─ artifacts under outputs/
        │
        ├─ SQLite 主数据轨
        │  └─ outputs/db/app.db
        │
        └─ Agent Service
           ├─ host-executed tools
           ├─ local OpenAI-compatible LLM runtime
           └─ tools/pi-cli bridge runtime
```

数据采用双轨存储：

| 轨道 | 位置 | 用途 |
|------|------|------|
| 原始数据 | `data/digital_marketing_campaign_dataset.csv` | 只读真相源 |
| 主数据轨 | `outputs/db/app.db` | API 查询、列表、按客户 ID 检索，可重建 |
| 产物轨 | `outputs/{models,metrics,explain,segments,rules,simulate,...}` | 模型、指标、解释、分群、规则、审计与报告 |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 22+ 与 npm
- Windows PowerShell、Git Bash、macOS 或 Linux shell 均可

### 1. 安装后端依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
# 可选：SHAP / mlxtend / imbalanced-learn
pip install -e ".[dev,ml]"
```

macOS / Linux / Git Bash 可使用：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. 准备数据库与分析产物

```powershell
python scripts/init_db.py
python scripts/import_campaigns.py

# P0 主线：清洗、训练、解释
python scripts/run_all.py

# P1：追加分群与规则
python scripts/run_all.py --with-p1

# 全量：E0-E8、PDP、预算模拟、分群对比
python scripts/run_all.py --with-p1 --full
```

### 3. 启动 API

```powershell
uvicorn digital_marketing.api.main:app --reload --port 9800
```

健康检查：

```powershell
curl http://127.0.0.1:9800/api/v1/health
```

Swagger 文档：

```text
http://127.0.0.1:9800/docs
```

### 4. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5600
```

前端默认 API 地址见 `frontend/.env.development`：

```text
VITE_API_BASE_URL=http://127.0.0.1:9800/api/v1
```

### 5. 可选：启用 PiAgent

```powershell
python scripts/setup_pi_cli.py
```

然后复制 `.env.example` 为 `.env` 并填写所需 Key：

```text
DEEPSEEK_API_KEY=...
OPENAI_BASE_URL=https://api.deepseek.com
```

也可以在 `/pi` 页面通过配置卡保存 Base URL、Bridge Model、Pi 路径和 API Key。密钥只落本地 `.env`，不会被 API 响应回显。

## 常用命令

| 命令 | 说明 |
|------|------|
| `python scripts/00_profile_data.py` | 生成数据画像 |
| `python scripts/01_clean_data.py` | 清洗、质量 flag、分层划分 |
| `python scripts/02_train_classify.py` | 基础分类实验 |
| `python scripts/03_explain_shap.py` | 全局解释产物 |
| `python scripts/04_train_cluster.py` | K-Means 分群 |
| `python scripts/05_mine_rules.py` | 关联规则挖掘 |
| `python scripts/06_train_full.py` | 全量 E0-E8 实验矩阵 |
| `python scripts/07_explain_advanced.py` | PDP/ICE 解释 |
| `python scripts/08_simulate_budget.py` | 预算模拟 |
| `python scripts/09_cluster_compare.py` | 多算法分群对比 |
| `python scripts/run_all.py --with-p1 --full` | 全量复现主流程 |
| `python scripts/export_paper_tables.py` | 导出论文表格 |
| `python scripts/setup_pi_cli.py` | 安装项目内 Pi SDK 与 bridge 依赖 |
| `pytest -q` | 后端测试 |
| `cd frontend; npm run build` | 前端类型检查与构建 |

## 前端页面

| 路由 | 页面 | 主要内容 |
|------|------|----------|
| `/screen` | 总览大屏 | 中央桑基图、外围小图、关键洞察 |
| `/` | 总览 Dashboard | KPI、渠道、转化分布、质量问题 |
| `/models` | 模型实验室 | E0-E8、PR/ROC、校准、lift、阈值成本 |
| `/customers` | 客户洞察 | 单客预测、SHAP、反事实敏感性 |
| `/segments` | 分群画像 | 簇画像、PCA、算法对比、稳定性 |
| `/rules` | 关联规则 | support、confidence、lift 表格 |
| `/simulate` | 预算模拟 | 期望价值曲线、推荐 K、Top 触达名单 |
| `/agent` | AI 分析台 | LLM 会话、工具轨迹、Markdown 回复、内联图表 |
| `/pi` | Pi 编排中枢 | PiAgent 配置、模型列表、健康、skills、审计 |
| `/about` | 关于与复现 | 数据来源、启动命令、AI 使用边界 |

## API 概览

所有接口统一前缀为 `/api/v1`，响应 envelope 为：

```json
{ "ok": true, "data": {}, "error": null, "request_id": "uuid" }
```

核心接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康状态、默认 run、产物状态 |
| GET | `/data/overview` | 数据总览 |
| GET | `/data/dashboard` | 大屏聚合数据与 `caliber` 口径 |
| GET | `/data/cross-matrix` | 渠道/类型/性别二维交叉转化率 |
| GET | `/models/metrics` | 模型指标与实验对比 |
| GET | `/models/curves` | PR/ROC 曲线 |
| GET | `/models/lift` | 十分位 lift 表 |
| GET | `/models/threshold-scan` | 成本敏感阈值扫描 |
| POST | `/models/predict` | 单条预测 |
| POST | `/models/predict/batch` | 批量预测，上限 200 |
| GET | `/explain/global` | 全局解释 |
| POST | `/explain/customer` | 单客局部解释 |
| GET | `/explain/pdp` | PDP/ICE 网格 |
| POST | `/explain/counterfactual` | 反事实敏感性分析 |
| GET | `/segments` | 分群概览 |
| GET | `/segments/compare` | 多算法分群对比 |
| GET | `/rules` | 关联规则 |
| POST | `/simulate/budget` | 预算模拟 |
| POST | `/agent/chat` | 普通 Agent 对话 |
| POST | `/agent/chat/stream` | SSE 流式 Agent 对话 |
| GET | `/agent/pi/config` | PiAgent 配置快照 |
| PUT | `/agent/pi/config` | 保存 PiAgent 配置 |
| GET | `/agent/pi/models` | 从上游获取可选模型列表 |
| GET | `/agent/pi/status` | Pi bridge 状态 |
| POST | `/agent/report` | 一键生成分析报告 |

完整契约以 `AGENTS.md` 为准。

## 项目结构

```text
.
├─ data/                         # 原始 CSV，只读真相源
├─ config/                       # settings/features/model/agent 配置
├─ src/digital_marketing/
│  ├─ api/                       # FastAPI routes 与 envelope 错误
│  ├─ core/                      # 配置、路径、日志
│  ├─ data/                      # 读取、清洗、质量、导入、split
│  ├─ features/                  # 特征构建与 schema
│  ├─ models/                    # 分类、集成、校准、指标
│  ├─ explain/                   # SHAP、PDP、反事实
│  ├─ segment/                   # 分群训练、分配、比较
│  ├─ rules/                     # 关联规则
│  ├─ simulate/                  # 预算模拟
│  ├─ services/                  # 产物加载与 dashboard 聚合
│  └─ agent/                     # 工具注册、LLM/local/Pi runtime、审计、报告
├─ frontend/                     # Vue 3 + Vite + Element Plus + ECharts
├─ scripts/                      # 数据、训练、解释、模拟、Pi 安装脚本
├─ tests/                        # pytest 测试
├─ docs/plans/                   # 实施计划与设计 token
├─ docs/reports/                 # 数据质量、论文指标等报告
├─ outputs/                      # 运行产物，默认 gitignore
└─ tools/pi-cli/                 # 项目内 Pi bridge，默认 gitignore node_modules
```

## 配置与安全

### 关键配置

| 文件 | 说明 |
|------|------|
| `config/settings.yaml` | 数据路径、输出目录、SQLite 路径、API 前缀、CORS |
| `config/features.yaml` | 丢弃列、可选列与后续分箱配置 |
| `config/model.yaml` | 模型与阈值相关配置 |
| `config/agent.yaml` | runtime、LLM、Pi 路径、工具白名单、审计目录 |
| `.env.example` | 本地环境变量模板 |

### 安全边界

- `.env`、API Key、模型大产物、SQLite DB、`node_modules` 不入库。
- 不覆盖 `data/` 原始 CSV；清洗结果写入 `outputs/processed/`。
- 不调用全局 `pi`；Pi 可执行文件必须在 `tools/pi-cli/` 下。
- LLM 不替代主分类器，不编造指标，不直接产生 chart-spec。
- 预算模拟与反事实分析均为模型行为或期望值口径，不构成因果收益承诺。

## 测试与验证

常用验证组合：

```powershell
pytest -q
cd frontend
npm run build
cd ..
git diff --check
```

当前基线：

- `pytest -q`：132 passed, 1 skipped
- `cd frontend; npm run build`：通过，仅 Vite chunk 大小提示
- `git diff --check`：通过

## 文档索引

| 文档 | 用途 |
|------|------|
| `AGENTS.md` | 架构、后端、数据/ML、Agent/Pi、安全与测试权威约束 |
| `DESIGN.md` | 前端页面、视觉、组件、图表和交互约束 |
| `CHANGE.md` | 变更日志 |
| `docs/plans/2026-08-02-Halo风格全量视觉改造计划.md` | Halo 全量视觉改造计划 |
| `docs/plans/Design Tokens.md` | 设计令牌说明 |
| `docs/reports/` | 数据质量、指标表、Pi 侦察等报告 |
| `scripts/demo_checklist.md` | 答辩演示脚本 |

## 许可与数据

本仓库代码采用 MIT License。原始数据位于 `data/`，请保持只读；运行产物位于 `outputs/`，默认不提交。若公开复用，请先确认数据集来源、模型产物和第三方 LLM/Pi SDK 的许可边界。
