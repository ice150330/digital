# 答辩演示 Checklist（约 8–10 分钟）

> 端口约定：**API `9800`** · **前端 `5600`**  
> 数字一律来自后端 / `outputs/`，禁止手改 metrics。

## 0. 开场前（2–5 分钟，答辩前完成）

```bash
# 后端
pip install -e ".[dev]"
python scripts/init_db.py
python scripts/import_campaigns.py
python scripts/run_all.py
python scripts/run_all.py --with-p1          # 分群 + 规则页有数
python scripts/setup_pi_cli.py               # 可选，项目内 Pi stub

uvicorn digital_marketing.api.main:app --reload --port 9800
```

```bash
# 前端（另开终端）
cd frontend
npm install
npm run dev
# → http://127.0.0.1:5600
```

自检：

| 检查 | 期望 |
|------|------|
| `GET http://127.0.0.1:9800/api/v1/health` | `ok=true`，`campaigns_count`≈8000，`artifacts_ok` |
| 浏览器打开 `:5600` | 顶栏 Health 绿点 |
| `pytest -q` | 全绿 |

## 1. 演示脚本（建议顺序）

| 分钟 | 页面 | 说什么 / 做什么 |
|------|------|----------------|
| 0:00 | 开场 | 双轨：CSV 只读 → SQLite 查询；模型/metrics **文件**不进库 |
| 0:30 | `/` 总览 | 样本量、正类比偏高 → 为何 **PR-AUC** 而非 Accuracy |
| 1:30 | `/models` | 表中 **PR-AUC** 高亮；指出 **Dummy** 行；Accuracy 标「仅对照」 |
| 3:00 | `/customers` | CustomerID 例：`8000` → proba / threshold / run_id；SHAP 条图 |
| 4:30 | `/customers` | （可选）批量 ID `8000,8001,8002`，说明上限 200、非因果 |
| 5:00 | `/agent` | runtime=`template`（无 Key 也可）；点芯片「各渠道转化率」；**展开 tool_trace** |
| 6:30 | `/segments` | Disclaimer：训练 **不含 Conversion**；簇转化率是事后统计 |
| 7:30 | `/rules` | lift 表；声明 **相关≠因果** |
| 8:30 | `/about` | 复现命令；论文数字以 `outputs/metrics` 为准 |
| 9:00 | 收尾 | 工具接地 Agent、Pi 仅 `tools/pi-cli/`、不扩大 P2 |

## 2. 备用话术（被问到时）

- **正类很高怎么办？** 并列 Dummy；主指标 PR-AUC；Accuracy 不作主结论。  
- **CustomerID / ConversionRate？** 永不入模 / 主模型默认不含；见特征 schema 与质量报告。  
- **Agent 会不会编 AUC？** 无工具结果不得写数字；看 tool_trace 与审计 jsonl。  
- **Pi 是什么？** 可选宿主；路径必须在项目 `tools/pi-cli/`；未装降级 template/local。  
- **因果吗？** 预测/分群/规则均 **非因果**；规则页与分群页有 Disclaimer。

## 3. 失败预案

| 现象 | 处理 |
|------|------|
| 前端空白 / 网络错误 | 确认 API 在 **:9800**；CORS 含 `http://127.0.0.1:5600` |
| 模型页无数据 | `python scripts/02_train_classify.py` 或 `run_all` |
| 客户页解释失败 | `python scripts/03_explain_shap.py`；或看 Swagger 样例 |
| 分群/规则空态 | `run_all --with-p1` 或 `04`/`05` 脚本 |
| Agent 无 Key | 保持 **template**；仍有真实工具结果 |
| Pi 未安装 | `setup_pi_cli.py` 或忽略，演示 template 即可 |
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
