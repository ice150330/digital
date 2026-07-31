# digital — 数字营销转化分析与 AI Copilot

本科毕业设计仓库：可复现的营销转化预测 / 可解释分析系统，外加工具接地的分析 Agent 与 **Pi 真实编排中枢**。

权威约束：

| 文档 | 职责 |
|------|------|
| [AGENTS.md](AGENTS.md) | 架构、后端、数据/ML、API、Agent、禁止项 |
| [DESIGN.md](DESIGN.md) | 仅前端设计系统 |
| [CHANGE.md](CHANGE.md) | 变更日志 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 会话入口 |
| [docs/plans/](docs/plans/) | 范围与里程碑 |

## 当前状态（2026-07-31）

**已落地（P0 + P1 + 阶段 9 + 2026-07-31 重构计划 Stage 1–6，可演示）：**

- 清洗 / 分层 split / 质量报告；**实验矩阵 E0–E8**（Dummy / Logistic / 默认树 / 不平衡权重 / SMOTE / 泄漏消融 / 去 flag 消融 / Stacking / 概率校准）；PR-AUC 主指标 + CV 5-fold + bootstrap 95% CI
- 增强评估：PR/ROC 曲线、lift 十分位、成本敏感阈值扫描、校准前后对比（Brier/ECE）
- 全局/局部解释（LightGBM `pred_contrib` 优先）+ PDP/ICE + 反事实（模型行为口径，非因果）
- 多算法分群对比（KMeans/GMM/Agglomerative）+ ARI 稳定性 + PCA 投影 + 自动画像名；关联规则
- 预算分配模拟器：期望值口径排序 + 推荐触达 K + Top 名单导出
- **L1 描述性分析（Stage 3）**：KPI 聚合 + 行为伪漏斗（横截面口径）+ 年龄/收入/支出分布 + 渠道×类型交叉矩阵（`/data/dashboard`、`/data/cross-matrix`）
- **`/screen` 总览大屏（Stage 3）**：全屏暗色作用域（`data-theme=screen`），KPI×6 / 伪漏斗 / 渠道 / 交叉热力 / 分布×3 / E0–E8 mini 榜 / SHAP Top8，答辩开场全景页
- **AI 会话图表（Stage 4）**：`render_chart` 声明式图表工具（9 数据集 × 6 图型，chart-spec v1.0 纯 JSON）+ 前端 `ChartCard` 内联渲染——对话即出图，数字全由宿主计算
- **Pi 真实编排（Stage 5，范式参考 VibeStart）**：同进程 SDK（`createAgentSession` + customTools 代理）；Pi 经 HTTP loopback 调用宿主 19 个工具（数字永不出宿主），默认 `runtime=pi`，任何失败自动降级 local 并标注
- **后端重构（Stage 1）**：`@tool` 装饰器一处定义（注册/规划/事实抽取/Pi 清单自动生效）；配置统一；运行时缓存
- **前端重构（Stage 2/6）**：`BaseChart` 封装 + 色板单一真相；侧栏四层叙事分组（总览大屏 → 描述性分析 → 预测建模 → 深度挖掘 → AI 与系统）+ 可折叠
- 前端**十路由**：**大屏** / 总览 / 模型 / 客户 / 分群 / 规则 / 预算模拟 / 分析台 / Pi 中枢 / 关于
- 演示：`scripts/demo_checklist.md`；论文表：`python scripts/export_paper_tables.py`（CV/CI/Brier 列）
- **端口：** API **9800** · 前端 **5600**
- **验证：** `pytest` **114 passed**（1 skipped 为 stub 环境专用）；`npm run build` 通过；Pi 桥接全链路实测联通（DeepSeek）

**P2 默认不做**（RAG、K8s、多租户、因果 uplift 主线等）。

## 双轨存储（必读）

```text
data/*.csv（只读真相源）
    → import → outputs/db/app.db     【主数据轨：查询/列表】
outputs/{models,metrics,explain,segments,rules,...}  【产物轨：文件；metrics 不进 SQLite】
```

禁止覆盖原始 CSV；禁止把 `app.db` 放进 `data/`。

## 快速上手（从零）

### 1. 后端

```bash
# 建议在项目根创建虚拟环境
python -m venv .venv
# Windows Git Bash:
source .venv/Scripts/activate

pip install -e ".[dev]"
# 可选：关联规则 mlxtend 等 → pip install -e ".[dev,ml]"

# 初始化库表并导入 CSV（默认全量重建 campaigns）
python scripts/init_db.py
python scripts/import_campaigns.py

# 分析流水线（P0）
python scripts/run_all.py
# 含分群 + 关联规则（P1）
python scripts/run_all.py --with-p1
# 全量矩阵 E0–E8 + PDP + 预算模拟 + 分群对比（阶段9）
python scripts/run_all.py --with-p1 --full

# 项目内 Pi SDK（默认安装 @earendil-works/pi-coding-agent + typebox；仅 tools/pi-cli/）
python scripts/setup_pi_cli.py

# 测试
pytest

# API
uvicorn digital_marketing.api.main:app --reload --port 9800
# 探测：curl http://127.0.0.1:9800/api/v1/health
```

可选环境变量见 [.env.example](.env.example)（`DIGITAL_ROOT`、`DIGITAL_DATABASE_URL` 等）。配置见 [config/](config/)。

**Pi 编排（可选但推荐）**：设置 LLM 凭证环境变量（如 `DEEPSEEK_API_KEY`），桥接默认用 `deepseek/deepseek-chat`（可用 `PI_BRIDGE_MODEL=provider/model` 覆盖）。无 Key 时 `runtime=pi` 自动降级 local，系统照常可用。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
# 浏览器打开 http://127.0.0.1:5600（大屏入口：/screen）
# 需后端已在 9800 端口；baseURL 见 frontend/.env.development
```

### 3. 常用脚本

| 命令 | 作用 |
|------|------|
| `python scripts/init_db.py` | 创建/确认 `outputs/db/app.db` 表结构 |
| `python scripts/import_campaigns.py` | 从 `data/*.csv` 导入 campaigns（默认 force 重建） |
| `python scripts/01_clean_data.py` | 清洗 → `outputs/processed/` + split + 质量报告 |
| `python scripts/02_train_classify.py` | 基础实验 E0/E1/E3 → `outputs/models` 与 `metrics` |
| `python scripts/06_train_full.py` | 全量矩阵 E0–E8（含消融/Stacking/校准 + CV/CI/曲线） |
| `python scripts/03_explain_shap.py` | 全局解释 → `outputs/explain` |
| `python scripts/07_explain_advanced.py` | PDP/ICE 网格 → `outputs/explain/pdp_*.json` |
| `python scripts/08_simulate_budget.py` | 预算模拟默认曲线 + Top-K 名单 → `outputs/simulate/` |
| `python scripts/04_train_cluster.py` | K-Means 分群（特征不含 Conversion） |
| `python scripts/09_cluster_compare.py` | 多算法分群对比 + 稳定性 + PCA 投影 |
| `python scripts/05_mine_rules.py` | 关联规则（相关≠因果） |
| `python scripts/run_all.py` | 清洗 → 训练 → 解释 |
| `python scripts/run_all.py --with-p1` | 上式 + 分群 + 规则 |
| `python scripts/run_all.py --with-p1 --full` | 全量（06 替代 02，追加 07/08/09） |
| `python scripts/setup_pi_cli.py` | 项目内安装 Pi SDK + 桥接依赖（`tools/pi-cli/`） |
| `python scripts/export_paper_tables.py` | 从 metrics 导出论文表（md+csv） |
| `scripts/demo_checklist.md` | 答辩演示脚本 |
| `pytest` | 后端测试（114 项） |

### 4. 演示路径（约 10–12 分钟）

0. **大屏开场** `/screen`：KPI / 伪漏斗 / 渠道 / 交叉 / 分布 / 模型榜 / SHAP 一页全景（横截面口径声明可见）
1. **总览** `/`：样本量、正类比、渠道、质量 issue
2. **模型** `/models`：E0–E8 对比表（CV/CI/Brier）+ PR/ROC + 校准 + 混淆矩阵 + lift + 阈值-成本滑块；指出 CI 重叠与消融行
3. **客户** `/customers`：ID 预测 + 局部解释（反事实面板默认收起，演示时展开；模型行为口径）
4. **预算模拟** `/simulate`：调价值/成本参数 → 推荐 K + Top 名单导出
5. **分析台** `/agent`：提问「画各渠道转化率柱状图」——Pi 真实编排宿主工具 + **会话内联图表**；展开 tool_trace 与五段契约
6. **Pi 中枢** `/pi`：runtime 状态（真实安装/bridge_ready）、skills、一键生成分析报告、审计回放
7. **分群 / 规则** `/segments` `/rules`：PCA 投影 + 稳定性徽章；Disclaimer 可见
8. **关于** `/about`：复现命令

失败预案：Swagger `http://127.0.0.1:9800/docs`；Pi 无 Key/桥接失败时自动降级 local 并在响应标注（`pi_fallback`），行为与纯 local 一致。

## 主要 API（前缀 `/api/v1`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 含 `artifacts_ok`、`default_run_id` |
| GET | `/data/overview` | 总览 |
| GET | `/data/dashboard` | 大屏聚合：KPI/伪漏斗/直方图 + `caliber` 口径 |
| GET | `/data/cross-matrix` | 二维交叉转化率（维度白名单 channel/type/gender） |
| GET | `/meta/features` | 入模特征 |
| GET | `/models/metrics` | 多 run；主字段 `pr_auc`（含 CV/CI/Brier） |
| GET | `/models/curves` `/models/lift` `/models/threshold-scan` `/models/calibration` | 评估曲线与校准 |
| POST | `/models/predict` | 单条：`proba/label/threshold/run_id` |
| POST | `/models/predict/batch` | 批量，上限 200 |
| GET | `/explain/global` | 全局解释 |
| POST | `/explain/customer` | 局部解释 |
| GET | `/explain/pdp` | PDP/ICE 网格 |
| POST | `/explain/counterfactual` | 反事实（模型行为口径） |
| GET | `/segments` `/segments/compare` `/segments/projection` | 分群 + 多算法对比 + PCA 投影 |
| POST | `/segments/assign` | 分配簇 |
| GET | `/rules` | 关联规则（可筛 lift） |
| POST | `/simulate/budget` | 预算分配模拟（期望值口径） |
| POST | `/agent/chat` | 工具接地对话（默认 runtime=pi，降级标注） |
| GET | `/agent/pi/status` | Pi 状态（installed/is_stub/bridge_ready/skills） |
| GET | `/agent/tools/manifest` | Pi 桥接工具清单（@tool 声明为唯一真相） |
| POST | `/agent/tool-run` | Pi 桥接 loopback 执行口（宿主 REGISTRY 实算） |
| GET | `/agent/audit/recent` | 审计行 |
| POST | `/agent/report` | 一键分析报告落盘 |

统一 envelope：`{ ok, data, error, request_id }`。细节以 [AGENTS.md](AGENTS.md) 为准。

## 技术栈（锁定）

- Python 3.11+、FastAPI、SQLAlchemy 2.0（同步 sqlite3）
- Vue 3 + Vite + TypeScript + Element Plus + ECharts + axios + vue-router（**npm**）
- 分类：scikit-learn、LightGBM；解释优先 `pred_contrib`（可选 shap）
- 规则：可选 mlxtend（`[ml]` extra）
- Agent：宿主 `@tool` 注册表（19 工具）+ 项目内 Pi SDK 桥接（`tools/pi-cli/`，同进程 `createAgentSession` + customTools 代理；禁止全局 `pi`）；node ≥ 22

## 许可与数据

原始数据集位于 `data/`，请保持只读；大产物与 `*.db` 默认不入库（见 `.gitignore`）。LLM Key 仅环境变量 / 本地 `.env`，仓库只留 `.env.example`。
