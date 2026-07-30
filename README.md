# digital — 数字营销转化分析与 AI Copilot

本科毕业设计仓库：可复现的营销转化预测 / 可解释分析系统，外加工具接地的分析 Agent。

权威约束：

| 文档 | 职责 |
|------|------|
| [AGENTS.md](AGENTS.md) | 架构、后端、数据/ML、API、Agent、禁止项 |
| [DESIGN.md](DESIGN.md) | 仅前端设计系统 |
| [CHANGE.md](CHANGE.md) | 变更日志 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 会话入口 |
| [docs/plans/](docs/plans/) | 范围与里程碑 |

## 当前状态（2026-07-30）

**已落地（P0 + P1 主线）：**

- 清洗 / 分层 split / 质量报告；E0 Dummy、E1 Logistic、E3 LightGBM；PR-AUC 主指标
- 全局/局部解释（LightGBM `pred_contrib` 优先）
- P0/P1 API：overview、metrics、predict、**batch**、explain、**segments**、**rules**、**agent**
- 前端七路由真数据页：总览 / 模型 / 客户 / 分群 / 规则 / 分析台 / 关于
- Local Agent（白名单工具 + 五段契约 + tool_trace + 审计）；无 Key → template
- 项目内 Pi：`python scripts/setup_pi_cli.py` → 仅 `tools/pi-cli/`（禁止全局 `pi`）

**可继续打磨：** 演示 checklist 深度、README 论文表导出、阶段 8 测试/文案；**P2 默认不做**。

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

# 可选：项目内 Pi stub
python scripts/setup_pi_cli.py

# 测试
pytest

# API
uvicorn digital_marketing.api.main:app --reload --port 8000
# 探测：curl http://127.0.0.1:8000/api/v1/health
```

可选环境变量见 [.env.example](.env.example)（`DIGITAL_ROOT`、`DIGITAL_DATABASE_URL`、`DIGITAL_LLM_API_KEY` / `OPENAI_API_KEY` 等）。配置见 [config/](config/)。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
# 浏览器打开 Vite 地址（默认 http://127.0.0.1:5173）
# 需后端已在 8000 端口；baseURL 见 frontend/.env.development
```

### 3. 常用脚本

| 命令 | 作用 |
|------|------|
| `python scripts/init_db.py` | 创建/确认 `outputs/db/app.db` 表结构 |
| `python scripts/import_campaigns.py` | 从 `data/*.csv` 导入 campaigns（默认 force 重建） |
| `python scripts/01_clean_data.py` | 清洗 → `outputs/processed/` + split + 质量报告 |
| `python scripts/02_train_classify.py` | E0/E1/E3 → `outputs/models` 与 `metrics` |
| `python scripts/03_explain_shap.py` | 全局解释 → `outputs/explain` |
| `python scripts/04_train_cluster.py` | K-Means 分群（特征不含 Conversion） |
| `python scripts/05_mine_rules.py` | 关联规则（相关≠因果） |
| `python scripts/run_all.py` | 清洗 → 训练 → 解释 |
| `python scripts/run_all.py --with-p1` | 上式 + 分群 + 规则 |
| `python scripts/setup_pi_cli.py` | 仅项目内 `tools/pi-cli/` Pi stub/安装 |
| `pytest` | 后端测试 |

### 4. 演示路径（约 8–10 分钟）

1. **总览** `/`：样本量、正类比、渠道、质量 issue  
2. **模型** `/models`：PR-AUC 主表 + Dummy 对照（Accuracy 仅对照）  
3. **客户** `/customers`：ID 预测 + 局部解释；可选批量 ID  
4. **分析台** `/agent`：芯片提问，展开 **tool_trace**（无 Key 也可用）  
5. **分群 / 规则** `/segments` `/rules`：Disclaimer 可见；需先 `--with-p1`  
6. **关于** `/about`：复现命令  

失败预案：Swagger `http://127.0.0.1:8000/docs`；Agent 选 template；Pi 未装时自动降级。

## 主要 API（前缀 `/api/v1`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 含 `artifacts_ok`、`default_run_id` |
| GET | `/data/overview` | 总览 |
| GET | `/meta/features` | 入模特征 |
| GET | `/models/metrics` | 多 run；主字段 `pr_auc` |
| POST | `/models/predict` | 单条：`proba/label/threshold/run_id` |
| POST | `/models/predict/batch` | 批量，上限 200 |
| GET | `/explain/global` | 全局解释 |
| POST | `/explain/customer` | 局部解释 |
| GET | `/segments` | 分群摘要 |
| POST | `/segments/assign` | 分配簇 |
| GET | `/rules` | 关联规则（可筛 lift） |
| POST | `/agent/chat` | 工具接地对话 |
| GET | `/agent/pi/status` | 项目内 Pi 状态 |

统一 envelope：`{ ok, data, error, request_id }`。细节以 [AGENTS.md](AGENTS.md) 为准。

## 技术栈（锁定）

- Python 3.11+、FastAPI、SQLAlchemy 2.0（同步 sqlite3）
- Vue 3 + Vite + TypeScript + Element Plus + ECharts + axios + vue-router（**npm**）
- 分类：scikit-learn、LightGBM；解释优先 `pred_contrib`（可选 shap）
- 规则：可选 mlxtend（`[ml]` extra）
- Agent：LocalToolRuntime + 可选项目内 Pi（`tools/pi-cli/`，禁止全局 `pi`）

## 许可与数据

原始数据集位于 `data/`，请保持只读；大产物与 `*.db` 默认不入库（见 `.gitignore`）。LLM Key 仅环境变量 / 本地 `.env`，仓库只留 `.env.example`。
