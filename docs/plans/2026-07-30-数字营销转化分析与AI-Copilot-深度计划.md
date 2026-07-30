# 第一版深度计划：数字营销转化分析与 AI Copilot 毕设

> **计划状态：** 终版（已修订：项目内 Pi CLI）  
> **仓库：** `f:\Project\digital`  
> **日期：** 2026-07-30  
> **修订：** Pi 不使用用户全局 CLI；由本项目 `scripts/setup_pi_cli.py` 拉取到 `tools/pi-cli/`，仅服务本地本仓库

---

## Context（为什么做）

`f:\Project\digital` 目前是**从零开始**的毕设仓库：仅有 MIT 许可、空 README、Python 模板 `.gitignore`，以及数字营销转化 CSV（`data/digital_marketing_campaign_dataset.csv`，8000×20，目标 `Conversion`）。无代码、依赖、API、前端或 Agent。

业务问题清晰：预测是否转化、解释关键因素、人群分群与规则挖掘、辅助营销决策。数据同时带有方法议题——正类约 **87.65%** 不平衡、常数广告字段、邮件/访问逻辑异常、`CustomerID` 疑似与标签相关——适合写进数据治理与实验设计。

你的目标不是 Jupyter 作业，而是：

> **算法与工程并重**：可复现的 Python 挖掘管线 + FastAPI/SPA 系统 + **系统内分析 Copilot**（开源 Pi 可插拔），且 AI **工具接地、可审计、可复现**。

**批准后意图产出：** 可运行全栈系统、实验产物、论文图表、答辩演示脚本。

---

## 已锁定决策

| 维度 | 决定 |
|------|------|
| 交付形态 | FastAPI + SPA + Agent |
| 前端 | **Vue 3 + Vite + Element Plus + ECharts**（契约可换 React，默认不换） |
| AI 深度 | 系统内 Copilot：NL → 受控工具 → grounded 回答 |
| LLM | 云端 OpenAI 兼容（默认 DeepSeek），Key 仅环境变量 |
| Pi | **项目内本地 Pi CLI**（自行拉取到仓库工具目录，**不使用**用户全局 `pi`）；现场可切换 Local / Pi Runtime，≥1–2 个 skill；**仅服务本项目本地演示** |
| 算法 | 四条都要：预测、SHAP、分群、关联规则（分层做深） |
| 学院导向 | 算法与工程并重 |
| 工期 | **5–6 个月+（按 24 周）** |

---

## 1. 题目与贡献

**题目：** 基于 Python 的数字营销客户转化分析与智能 Agent 辅助决策系统  

**副标题：** Digital Marketing Conversion Analytics with a Tool-Grounded AI Copilot (Pluggable Pi Runtime)

**一句话贡献：**  
在可复现的不平衡转化预测、SHAP 解释、客户分群与关联规则之上，构建 FastAPI + Vue 分析系统，并以受控工具调用的 Copilot（支持 Pi 运行时切换）将指标与模型转化为可审计的营销建议。

**答辩一句话：**  
“不只是一个分类器，而是数据治理 → 可解释决策的闭环，并用 Agent 把结果变成可追问、可核对的分析台。”

---

## 2. 范围分层（严格优先级）

### P0 — MVP（约第 10 周必须可演示）

- 数据加载、清洗、质量报告、核心 EDA  
- 转化预测：Dummy + Logistic + LightGBM/RF；分层验证；**PR-AUC / F1 / 混淆矩阵**  
- 全局 SHAP + 单客户解释 API  
- FastAPI：health、数据概览、指标、预测、解释  
- Vue：总览、模型评估、客户解释、Agent 对话（基础）  
- `LocalToolRuntime`：≥5 工具 + `outputs/agent_logs/*.jsonl`  
- `scripts/run_all.py` 一键产出 metrics  

### P1 — 完整版（答辩主路径）

- 客户分群（K-Means，可选 GMM）+ 簇画像与策略卡片  
- 关联规则（分箱 + mlxtend）+ Lift 过滤与解读  
- 代价敏感阈值 / 触达名单导出  
- Agent 覆盖分群/规则/策略；四段式输出契约  
- **项目内 Pi CLI 拉取与隔离** + PiRuntime 切换 + 2 个 marketing skills
- README、OpenAPI、演示脚本

### P2 — 加分

- Agent 黄金评测集 30–50 问 + 自动打分  
- 报告导出（MD/PDF）  
- 渠道统计检验与简单预算建议  
- Docker Compose  
- `ConversionRate` 泄漏消融专章  
- 概率校准、what-if（明确非因果）  
- 会话历史 UI / 简易登录（非必须）  

**延期可砍顺序：** P2 → 关联规则改为“论文有表 + 只读 API” → 项目内 Pi 改为架构说明+录屏 → 前端美化。  
**永不砍：** 数据协议、分类主实验、SHAP、可运行 API、防泄漏叙述。  
**Pi 约束（硬性）：** 只使用 `tools/pi-cli/`（或等价项目目录）内安装的 CLI；禁止调用用户 PATH 上的全局 `pi`；该 CLI **仅服务本仓库本地**，不做系统级安装、不改用户全局配置。

---

## 3. 算法：做深 / 做有

| 主线 | 优先级 | 做深 | 最低做有 |
|------|--------|------|----------|
| 转化预测+不平衡 | P0 核心 | 多模型、class_weight/阈值/可选 SMOTE、校准讨论 | 3 模型 + PR-AUC 表 |
| SHAP | P0 核心 | 全局/局部、案例叙事模板 | TopK + 单客户贡献 |
| 客户分群 | P1 做深 | 标准化、选 K、簇×渠道×转化策略 | K-Means + 簇转化率 |
| 关联规则 | P1 做实 | 分箱、Lift、业务解读 | TopN 规则表 |

**不做主线：** 深度因果 uplift、向量 RAG、多 Agent 辩论、K8s/多租户。

---

## 4. 目标架构

```
Vue 3 SPA  ──REST──►  FastAPI /api/v1/*
                         ├─ data | models | explain
                         ├─ segment | rules | agent
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Analysis Core          Agent Layer
   clean/features/train     tools + prompts + skills
   shap/cluster/rules       LocalToolRuntime (默认)
              │             PiRuntime ──► tools/pi-cli/ (项目内 CLI)
              └──────────► outputs/artifacts
                    models metrics figures agent_logs
```

### 目录结构

```
digital/
├── data/                          # 原始 CSV（只读源）
├── config/
│   ├── settings.yaml              # 路径、seed、split
│   ├── features.yaml              # 入模/丢弃/分箱
│   ├── model.yaml
│   └── agent.yaml                 # runtime: local|pi；pi_bin 指向项目内路径
├── tools/
│   └── pi-cli/                    # ★ 项目内 Pi CLI（脚本拉取，不进用户全局）
│       ├── .gitkeep
│       ├── README.md              # 版本、来源、仅本地用途说明
│       └── ...                    # npm/npx 本地安装产物或 vendor 目录（gitignore 大体积）
├── src/digital_marketing/         # 可安装包名，避免 src 裸堆
│   ├── core/                      # config, paths, seed, logging
│   ├── data/                      # load, clean, quality, split
│   ├── features/                  # build, schema
│   ├── models/                    # classify, imbalance, registry
│   ├── explain/                   # shap global/local
│   ├── segment/                   # cluster + profiles
│   ├── rules/                     # association
│   ├── agent/
│   │   ├── tools/
│   │   ├── prompts/
│   │   ├── skills/                # Pi skills（本项目专用）
│   │   ├── local_runtime.py
│   │   ├── pi_runtime.py          # 只调用 tools/pi-cli 下二进制
│   │   ├── grounding.py
│   │   ├── audit.py
│   │   └── service.py
│   ├── api/                       # FastAPI routers + main
│   └── schemas/                   # pydantic
├── frontend/                      # Vue3 + Vite
├── scripts/
│   ├── run_all.py
│   ├── setup_pi_cli.py            # ★ 拉取/安装项目内 Pi CLI
│   ├── 00_profile_data.py
│   ├── 01_clean_data.py
│   ├── 02_train_classify.py
│   ├── 03_train_cluster.py
│   ├── 04_mine_rules.py
│   └── demo_checklist.md
├── notebooks/                     # 仅探索；逻辑回流 src
├── tests/
├── outputs/ 或 artifacts/         # gitignore 大文件
├── docs/plans/  docs/reports/
├── .env.example
├── requirements.txt
└── README.md
```

**原则：** 分析内核与 Agent 分离；Runtime 可插拔；论文表只认 `outputs/metrics`。  
**Pi 隔离原则：** CLI 落在 `tools/pi-cli/`，由 `scripts/setup_pi_cli.py` 拉取固定版本；`pi_runtime.py` **禁止** `which pi` / PATH 回退到用户全局安装。

---

## 5. 数据与实验设计

### 5.1 处理策略

| 字段/问题 | 策略 |
|-----------|------|
| CustomerID | **永不入模**（标识符；注意与标签相关性，防泄漏质疑） |
| AdvertisingPlatform/Tool | **删除**（常数） |
| ConversionRate | **主模型默认不含**；E5 消融含/不含 |
| EmailClicks > EmailOpens | 主实验：保留 + `email_inconsistent` 标志；可选 cap 敏感性 |
| WebsiteVisits=0 仍有深度 | `invalid_web_metrics_flag`；主实验固定一种修正并写报告 |
| 类别特征 | One-Hot / 树模型原生类别（实现时统一 schema） |

### 5.2 验证协议（硬约束）

1. **先 split，后 fit**；分层 train/valid/test 或 Stratified K-Fold + holdout  
2. imputer/scaler/encoder/**SMOTE 只在 train 拟合**  
3. 阈值只在 valid 搜索，test **一次性**评估  
4. 固定 `random_seed`；导出 `feature_schema.json`  
5. 推理校验字段一致性  

### 5.3 分类实验矩阵

| ID | 内容 | 目的 |
|----|------|------|
| E0 | Dummy 多数类 | 下限 |
| E1 | Logistic + class_weight | 可解释基线 |
| E2 | RF/LightGBM 默认 | 非线性 |
| E3 | 树模型 + 不平衡权重 | **主方案候选** |
| E4 | E3 + SMOTE（仅 train） | 采样对比 |
| E5 | 最优 ± ConversionRate | 泄漏/信息消融 |
| E6 | 最优 ± 质量 flag | 数据质量特征 |

**主指标顺序：** PR-AUC → ROC-AUC → F1 / Recall@Precision → 混淆矩阵；Accuracy 仅反面教材。

### 5.4 分群与规则

- 分群：**训练不含 Conversion**；事后统计簇转化率；K 用轮廓/肘部 + 可解释性  
- 规则：分箱 itemset；min_support/confidence/lift；UI/论文标明**相关非因果**  

### 5.5 复现

```text
python scripts/run_all.py
uvicorn src.digital_marketing.api.main:app --reload
cd frontend && npm run dev
```

---

## 6. Agent / Copilot

### 6.1 用例

1. 各渠道转化率对比与预算直觉  
2. 单客户高/低转化的 SHAP 叙事  
3. 高 AdSpend 人群的活动类型差异  
4. 某簇画像与触达建议  
5. Lift Top 规则解读  

### 6.2 工具

| 阶段 | 工具 |
|------|------|
| P0 | `get_dataset_profile`, `get_data_quality_issues`, `conversion_by_dimension`, `get_model_metrics`, `predict_proba`, `explain_global`, `explain_customer`, `get_feature_schema` |
| P1 | `segment_summary`, `assign_cluster`, `top_association_rules`, `strategy_brief` |
| P2 | `compare_experiments` |

### 6.3 输出契约

`observed_facts` / `inferences` / `recommendations` / `open_questions` / `tool_trace`

### 6.4 Runtime

- **LocalToolRuntime（默认）：** DeepSeek 选工具 + 组织语言；Python 执行工具（**Host-executed tools**）  
- **PiRuntime（演示）：** 仅调用**项目内** Pi CLI，例如：  
  `tools/pi-cli/node_modules/.bin/pi -p --mode json --skill src/digital_marketing/agent/skills/...`  
  （具体相对路径以 `setup_pi_cli` 安装结果为准，写入 `config/agent.yaml` 的 `pi.executable`）  
  同样只调白名单工具；失败降级 Local  
- 配置与前端均可切换 `local | pi`  
- **无 Key：** 关键词/规则路由 + 模板播报工具 JSON（离线可演示）  

### 6.4.1 项目内 Pi CLI（本地专用，不依赖用户全局）

| 项 | 约定 |
|----|------|
| 安装位置 | `tools/pi-cli/`（仓库内；安装产物可 gitignore） |
| 安装方式 | `python scripts/setup_pi_cli.py`：用 **npm/pnpm 本地安装** `@earendil-works/pi-coding-agent@<锁定版本>` 到该目录，或官方安装脚本指定 prefix 到该目录 |
| 版本锁定 | `tools/pi-cli/package.json` + lockfile（或 `VERSION` 文件）固定版本，保证答辩可复现 |
| 调用方式 | `PiRuntime` 只读配置项 `pi.executable`（绝对/相对项目根路径），**禁止**使用用户 PATH 中的 `pi` |
| 作用域 | **仅服务本项目本地演示与开发**；不写入用户全局 npm、不修改用户 shell 配置 |
| 工作目录 | 子进程 `cwd` 固定为项目根或沙箱子目录；session 写入 `outputs/agent_sessions/` |
| 配置隔离 | 若 Pi 支持自定义配置/session 目录，一律指向项目内路径（如 `tools/pi-cli/config`、`outputs/agent_sessions`），避免读写 `~/.pi` 等用户家目录（若上游强制写家目录，须在文档说明并尽量用环境变量重定向） |
| 未安装时 | `/agent` 切换 pi 返回明确错误：提示运行 `setup_pi_cli.py`；自动降级 `local` |
| 与用户自有 Pi 关系 | **零耦合**：即使用户本机已装全局 Pi，本系统也不调用 |

### 6.5 审计与安全

- `outputs/agent_logs/` 或 `logs/audit/*.jsonl`  
- 不写回原始 `data/`；不把 Key 进库  
- 禁止未 grounding 的数字；失败明说不可获取  
- 项目内 Pi 子进程：超时、输出长度限制；工具白名单与 Local 一致  

### 6.6 Pi 演示技能（P1）

1. `channel-conversion-compare`  
2. `customer-shap-narrative`  
（技能文件放在本仓库 `src/.../agent/skills/`，由项目内 CLI 的 `--skill` 加载。） 

---

## 7. API 与前端

### API（`/api/v1`）

| 方法 | 路径 | 阶段 |
|------|------|------|
| GET | `/health` | P0 |
| GET | `/data/overview` | P0 |
| GET | `/meta/features` | P0 |
| GET | `/models/metrics` | P0 |
| POST | `/models/predict` | P0 |
| GET/POST | `/explain/global`, `/explain/customer` | P0 |
| GET/POST | `/segments`, `/segments/assign` | P1 |
| GET | `/rules` | P1 |
| POST | `/agent/chat` | P0 |
| GET | `/agent/sessions/{id}` | P0 |
| POST | `/agent/runtime` | P1 |
| GET | `/agent/pi/status` | P1：项目内 CLI 是否已安装、版本、路径（非用户全局） |

统一 envelope；预测回传 `run_id` + `threshold`；解释回传 `top_features[]`。

### SPA 页面

1. 总览 Dashboard  
2. 模型实验室  
3. 客户洞察（预测+SHAP）  
4. 分群画像  
5. 关联规则  
6. AI 分析台（对话 + Runtime + trace）  
7. 关于/复现/AI 使用说明  

预置 2–3 个答辩样例客户（高/低概率可讲故事）。

---

## 8. 24 周里程碑

| 周 | 里程碑 | 出口 |
|----|--------|------|
| 1–2 | M0 骨架+开题 | 可安装、可加载数据、开题大纲 |
| 3–5 | M1 数据治理+EDA | clean + 质量报告 v1 |
| 6–8 | M2 预测 E0–E4 | metrics + artifact |
| 9–10 | M3 SHAP + API 骨架 | `/explain`；**P0 演示雏形** |
| 11–13 | M4 分群+规则 | 产物 + API |
| 14–16 | M5 API 完备 | OpenAPI |
| 15–18 | M6 Vue 联调 | 六页面可用 |
| 17–20 | M7 Local Copilot | 工具+日志+契约 |
| 19–21 | M8 项目内 Pi CLI + 插拔 | `setup_pi_cli`、隔离调用、切换演示 |
| 20–23 | M9 论文与评测 | 实验章、PPT、可选评测集 |
| 23–24 | M10 打磨 | README、录屏、彩排 |

**并行：** M4 ∥ API；M6 ∥ M7。  
**阶段门禁：** 每阶段必须有可运行命令或可打开页面。

---

## 9. 技术栈

| 层 | 选择 |
|----|------|
| Python 3.11+ | pandas, sklearn, lightgbm, shap, mlxtend |
| API | FastAPI, uvicorn, pydantic v2 |
| 前端 | Vue 3, Vite, Element Plus, ECharts, axios |
| LLM | DeepSeek OpenAI 兼容 |
| Agent 开源 | **项目内** Pi CLI（`@earendil-works/pi-coding-agent` 锁定版本，如 0.78.x），经 `tools/pi-cli/` 本地安装 |
| 测试 | pytest（含「pi 路径必须在 tools/pi-cli 下」的断言） |
| 配置 | YAML + env |

---

## 10. 风险与学术诚信

| 风险 | 缓解 |
|------|------|
| 范围过大 | P0/P1/P2；第 10 周冻结 MVP |
| 全预测 1 仍高 Accuracy | Dummy + PR-AUC + 阈值专节 |
| ID/ConversionRate 泄漏质疑 | 剔除/消融 + 论文专节 |
| LLM 幻觉 | 工具强制、契约、日志 |
| 项目内 Pi 拉取失败/版本变动 | 锁定 package 版本；默认 Local；录屏备份；status 接口提示 setup |
| 误用用户全局 pi | `pi_runtime` 禁止 PATH 回退；测试校验 executable 前缀 |
| 学术不端质疑 | AI 使用附录；数字可复现；本人可脱稿 |
| 密钥泄露 | `.env` + gitignore |

**表述红线：** 相关 ≠ 因果；不编造上线收益；Agent 展示 tool_trace。

---

## 11. 验收与 8–10 分钟演示脚本

### 验收

1. README 可复现训练与启动  
2. 演示路径：总览 → 模型对比 → 单客户 SHAP → Agent 问答 →（可选）项目内 Pi 切换  
3. Agent 含数字且 trace 可见  
4. 论文主表 = `outputs/metrics`  
5. 质量/不平衡/泄漏有专节  
6. 分群与规则至少页面或报告可见  
7. pytest 关键路径通过  
8. `GET /agent/pi/status` 显示的可执行文件路径位于 `tools/pi-cli/`，且**不等于**用户全局 `pi` 

### 演示脚本

1. **1 min** 背景与不平衡  
2. **1.5 min** 质量坑与防泄漏  
3. **2 min** E0 vs 主模型；PR-AUC；阈值  
4. **2 min** 在线预测 + SHAP 故事  
5. **1.5 min** 分群/规则（完整版）  
6. **1 min** Copilot + tool trace（可切**项目内** Pi，并展示本地路径） 
7. **1 min** 贡献、局限、展望  

**失败预案：** 前端挂 → Swagger；SHAP 慢 → 预缓存样例；无 Key → 模板模式。

---

## 12. 论文章节建议

1. 绪论  
2. 相关技术  
3. 需求与总体设计  
4. 数据治理与特征  
5. 挖掘与建模实验  
6. 系统实现（API/前端/Agent/Pi）  
7. 测试与分析  
8. 总结与展望  
附录：复现、AI 使用说明、数据字典  

---

## 13. 批准后首批实现任务

1. 目录、`requirements.txt`、`.env.example`、`.gitignore` 增强、README  
2. `src/digital_marketing/data/*` + pytest  
3. 质量报告 → `docs/reports/`  
4. 最小训练闭环 → `outputs/metrics`  
5. FastAPI health + overview  
6. Vue 脚手架 + 总览对接  

**计划未批准前不修改业务仓库。**

---

## 14. 默认项（不阻塞开工）

| 项 | 默认 |
|----|------|
| 前端 | Vue 3 |
| 登录 | 无（本地演示） |
| 主树模型 | LightGBM（装不上则 RF） |
| ConversionRate | 主模型不含，E5 消融 |
| 分群 vs 规则 | 分群优先做深，规则做实 |
| 包管理 | requirements.txt 起步 |

---

## 验证方式（实现后）

- `pytest`  
- `python scripts/run_all.py`  
- `python scripts/setup_pi_cli.py` 后 `tools/pi-cli` 内可执行  
- API + 前端演示 checklist  
- 5 个标准 Agent 问题人工对数  
- 项目内 Pi 至少成功一次或文档 fallback；确认未调用全局 `pi` 

---

## 关键路径

- 数据源：`data/digital_marketing_campaign_dataset.csv`  
- 将创建：`src/digital_marketing/**`、`frontend/**`、`config/**`、`scripts/**`（含 `setup_pi_cli.py`）、`tools/pi-cli/**`、`tests/**`、`docs/**`  
- 将更新：`README.md`、`.gitignore`（忽略 `tools/pi-cli/node_modules` 等安装产物，保留 lock/VERSION 与说明） 

---

**请批准本计划。** 若需微调（例如前端改 React、关联规则降为 P2），在批准时注明即可。
