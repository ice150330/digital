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

## 当前状态（脚手架）

已完成 **第一步：框架搭建 + SQLite 初始化**：

- 可安装 Python 包 `digital_marketing`（`src/`）
- SQLite 主数据轨：`outputs/db/app.db`（CSV 导入，可重建）
- FastAPI `GET /api/v1/health`（统一 envelope）
- Vue3 空壳：顶栏健康点 + 侧栏占位 + 首页联调 health

**尚未实现：** 清洗/训练、SHAP、业务 API、完整业务页、Agent/Pi。

## 双轨存储（必读）

```text
data/*.csv（只读真相源）
    → import → outputs/db/app.db     【主数据轨：查询/列表】
outputs/{models,metrics,...}         【产物轨：文件；metrics 不进 SQLite】
```

禁止覆盖原始 CSV；禁止把 `app.db` 放进 `data/`。

## 快速上手

### 1. 后端

```bash
# 建议在项目根创建虚拟环境
python -m venv .venv
# Windows Git Bash:
source .venv/Scripts/activate

pip install -e ".[dev]"

# 初始化库表并导入 CSV（默认全量重建 campaigns）
python scripts/init_db.py
python scripts/import_campaigns.py

# 测试
pytest
pytest tests/test_health.py          # 单文件
pytest tests/test_health.py::test_health_ok_with_data  # 单用例（名称以文件为准）

# API
uvicorn digital_marketing.api.main:app --reload --port 8000
# 探测：curl http://127.0.0.1:8000/api/v1/health
```

可选环境变量见 [.env.example](.env.example)（`DIGITAL_ROOT`、`DIGITAL_DATABASE_URL` 等）。配置见 [config/settings.yaml](config/settings.yaml)。

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
| `python scripts/import_campaigns.py --no-force` | 非强制（行为以实现为准） |
| `pytest` | 后端测试 |

## 技术栈（锁定）

- Python 3.11+、FastAPI、SQLAlchemy 2.0（同步 sqlite3）
- Vue 3 + Vite + TypeScript + Element Plus + axios + vue-router
- 后续：LightGBM/RF、SHAP、项目内 Pi（`tools/pi-cli/`，禁止全局 `pi`）

## 许可与数据

原始数据集位于 `data/`，请保持只读；大产物与 `*.db` 默认不入库（见 `.gitignore`）。
