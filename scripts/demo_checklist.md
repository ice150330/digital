# 答辩演示 Checklist（约 8–10 分钟）

> 端口约定：**API `9800`** · **前端 `5600`**  
> 数字一律来自后端 / `outputs/`，禁止手改 metrics。

## 0. 开场前（2–5 分钟，答辩前完成）

```bash
# 后端
pip install -e ".[dev]"
python scripts/init_db.py
python scripts/import_campaigns.py
python scripts/run_all.py --with-p1 --full   # 全量矩阵 + 分群 + 规则，各页有数
python scripts/setup_pi_cli.py               # 项目内 Pi SDK（真实安装）

# Pi 编排（可选但推荐）：设置 LLM 凭证
export DEEPSEEK_API_KEY=sk-...               # Windows cmd: set DEEPSEEK_API_KEY=...
# 无 Key 也能演示：runtime=pi 自动降级 local，行为一致

uvicorn digital_marketing.api.main:app --reload --port 9800
```

```bash
# 前端（另开终端）
cd frontend
npm install
npm run dev
# → http://127.0.0.1:5600（大屏入口：/screen）
```

自检：

| 检查 | 期望 |
|------|------|
| `GET http://127.0.0.1:9800/api/v1/health` | `ok=true`，`campaigns_count`≈8000，`artifacts_ok` |
| `GET http://127.0.0.1:9800/api/v1/agent/pi/status` | `installed=true`、`bridge_ready=true`（有 Key 时演示真实 Pi） |
| 浏览器打开 `:5600/screen` | 大屏各板块有数 |
| `pytest -q` | 全绿（114 passed） |

## 1. 演示脚本（建议顺序）

| 分钟 | 页面 | 说什么 / 做什么 |
|------|------|----------------|
| 0:00 | `/screen` 大屏 | **开场全景**：KPI / 伪漏斗（横截面口径声明）/ 渠道 / 交叉 / 分布 / E0–E8 榜 / SHAP；一句带过「数据分析→数据挖掘由浅入深」的导航分层 |
| 1:00 | 开场白 | 双轨：CSV 只读 → SQLite 查询；模型/metrics **文件**不进库 |
| 1:30 | `/` 总览 | 样本量、正类比偏高 → 为何 **PR-AUC** 而非 Accuracy |
| 2:30 | `/models` | 表中 **PR-AUC** 高亮；指出 **Dummy** 行与 E5/E6 消融行；CI 重叠不宣称更优 |
| 4:00 | `/customers` | CustomerID 例：`8000` → proba / threshold / run_id；SHAP 条图；（可选）展开反事实面板说明模型行为口径 |
| 5:00 | `/agent` | 提问「**画各渠道转化率柱状图**」→ **Pi 真实编排**宿主工具 + **会话内联出图**；展开 tool_trace 与五段契约（无 Key 时自动降级，同样有图） |
| 6:30 | `/pi` | Pi 状态（真实安装 / bridge_ready）、skills、一键报告、审计回放 |
| 7:30 | `/segments` | Disclaimer：训练 **不含 Conversion**；簇转化率是事后统计；PCA 投影 + 稳定性 |
| 8:30 | `/rules` `/simulate` | lift 表（相关≠因果）；预算模拟调参 → 推荐 K + 名单导出（期望值口径） |
| 9:30 | `/about` 收尾 | 复现命令；工具接地（数字永不出宿主）、Pi 仅 `tools/pi-cli/`、不扩大 P2 |

## 2. 备用话术（被问到时）

- **正类很高怎么办？** 并列 Dummy；主指标 PR-AUC；Accuracy 不作主结论。  
- **CustomerID / ConversionRate？** 永不入模 / 主模型默认不含；见特征 schema 与质量报告。  
- **Agent 会不会编 AUC？** 无工具结果不得写数字；看 tool_trace 与审计 jsonl；Pi 的工具调用经 loopback 回宿主实算（`noTools:'builtin'` 禁掉 Pi 内置文件/shell 工具）。  
- **Pi 是什么？** `@earendil-works/pi-coding-agent` SDK 同进程桥接（范式参考 VibeStart）；路径必须在项目 `tools/pi-cli/`；桥接失败自动降级 local 并标注。  
- **AI 会话出的图可信吗？** `render_chart` 返回声明式 spec，数据由宿主计算、色板前端统一，LLM/Pi 永不产数字也永不产 spec。  
- **因果吗？** 预测/分群/规则均 **非因果**；伪漏斗为横截面口径；规则页与分群页有 Disclaimer。

## 3. 失败预案

| 现象 | 处理 |
|------|------|
| 前端空白 / 网络错误 | 确认 API 在 **:9800**；CORS 含 `http://127.0.0.1:5600` |
| 模型页无数据 | `python scripts/02_train_classify.py` 或 `run_all` |
| 客户页解释失败 | `python scripts/03_explain_shap.py`；或看 Swagger 样例 |
| 分群/规则空态 | `run_all --with-p1` 或 `04`/`05` 脚本 |
| Agent 无 Key | runtime=pi 自动降级 local；仍有真实工具结果与图表 |
| Pi 桥接异常 | 响应含 `pi_fallback` 标注即已降级；或临时 `POST /agent/runtime` 切 local |
| 现场装依赖慢 | 预先 `npm run build` + 录屏备份；Swagger：`http://127.0.0.1:9800/docs` |

## 4. 论文数字核对

```bash
python scripts/export_paper_tables.py
# → docs/reports/*-论文指标表.md
# → outputs/metrics/paper_leaderboard.csv
```

**禁止**手抄与 `outputs/metrics/*.json` 不一致的表。

## 5. 演示后自检

- [ ] 未修改 `data/*.csv`  
- [ ] metrics 仍在 `outputs/metrics/`，不在 SQLite  
- [ ] Agent 日志在 `outputs/agent_logs/`（若点过分析台）  
- [ ] 未提交 `.env` / Key  
