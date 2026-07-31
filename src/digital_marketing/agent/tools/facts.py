"""工具结果 → 可引用事实字符串的抽取器（Stage 1 自 grounding.facts_from_tool 逐字搬迁）。

每个函数签名 (payload: dict) -> list[str]，payload 为 run_tool 的完整返回
{ok, tool, result|error}；not-ok 与兜底分派由 grounding.facts_from_tool 统一处理。
红线：仅基于工具结果抽数字，不编造。
"""

from __future__ import annotations

from typing import Any


def dataset_profile(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = []
    if r.get("n_rows") is not None:
        out.append(f"样本量 n_rows={r['n_rows']}")
    if r.get("positive_rate") is not None:
        out.append(f"正类占比 positive_rate={float(r['positive_rate']):.4f}")
    return out


def data_quality_issues(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [f"质量 issue 条数={r.get('issue_count')}"]
    for it in (r.get("issues") or [])[:5]:
        out.append(f"issue {it.get('code')}: count={it.get('count')}")
    return out


def conversion_by_dimension(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = []
    dim = r.get("dimension")
    for it in (r.get("items") or [])[:6]:
        out.append(
            f"{dim}={it.get('key')}: n={it.get('n')}, conversion_rate={float(it.get('conversion_rate') or 0):.4f}"
        )
    return out


def model_metrics(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = []
    items = r.get("items") or ([r] if r.get("run_id") else [])
    for it in items[:5]:
        out.append(
            f"run={it.get('run_id')} PR-AUC={it.get('pr_auc')} ROC-AUC={it.get('roc_auc')} "
            f"Accuracy(对照)={it.get('accuracy')}"
        )
    if r.get("accuracy_note"):
        out.append(str(r["accuracy_note"]))
    return out


def feature_schema(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    cols = r.get("feature_columns_raw") or []
    return [f"入模原始特征数={len(cols)}；永不入模={r.get('never_features')}"]


def predict_proba(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    return [
        f"proba={r.get('proba')}, label={r.get('label')}, threshold={r.get('threshold')}, run_id={r.get('run_id')}"
    ]


def explain_global(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [f"全局解释 method={r.get('method')} run_id={r.get('run_id')}"]
    for f in (r.get("top_features") or [])[:5]:
        out.append(f"特征 {f.get('name')} mean_abs={f.get('mean_abs_shap')}")
    return out


def explain_customer(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [
        f"客户解释 method={r.get('method')} proba={r.get('proba')} run_id={r.get('run_id')}"
    ]
    for f in (r.get("top_features") or [])[:5]:
        out.append(f"{f.get('name')} shap={f.get('shap_value')}")
    return out


def segment_summary(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [f"分群 k={r.get('n_clusters')} method={r.get('method')}"]
    for c in (r.get("clusters") or [])[:8]:
        out.append(
            f"簇 {c.get('cluster_id')}: n={c.get('n')}, conversion_rate(事后)={c.get('conversion_rate')}"
        )
    return out


def assign_cluster(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    return [f"分配簇 cluster_id={r.get('cluster_id')} distance={r.get('distance')}"]


def top_association_rules(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [r.get("disclaimer") or "规则相关非因果"]
    for rule in (r.get("rules") or [])[:5]:
        out.append(
            f"{rule.get('antecedents')} => {rule.get('consequents')} "
            f"support={rule.get('support')} conf={rule.get('confidence')} lift={rule.get('lift')}"
        )
    return out


def compare_experiments(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [f"实验数 n={r.get('n_runs')}，默认 run={r.get('default_run_id')}"]
    for it in (r.get("items") or [])[:8]:
        cv = it.get("cv_pr_auc_mean")
        ci = (it.get("pr_auc_ci_low"), it.get("pr_auc_ci_high"))
        tag = "（消融，不作默认）" if it.get("ablation") else ""
        out.append(
            f"run={it.get('run_id')} PR-AUC={it.get('pr_auc')}"
            + (f" CV={cv:.4f}±{it.get('cv_pr_auc_std'):.4f}" if cv is not None else "")
            + (f" CI=[{ci[0]:.4f},{ci[1]:.4f}]" if None not in ci else "")
            + tag
        )
    if r.get("note"):
        out.append(str(r["note"]))
    return out


def calibration_summary(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    return [
        f"校准 run={r.get('run_id')} method={r.get('method')} "
        f"brier {r.get('brier_before')}→{r.get('brier_after')} "
        f"ece {r.get('ece_before')}→{r.get('ece_after')}"
    ]


def lift_table(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [f"lift 表 run={r.get('run_id')}"]
    for d in (r.get("lift_deciles") or [])[:3]:
        out.append(
            f"十分位 {d.get('decile')}: n={d.get('n')}, 累计捕获率={d.get('capture_rate'):.4f}, lift={d.get('lift'):.4f}"
        )
    return out


def simulate_budget(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    p = r.get("params") or {}
    out: list[str] = [
        f"预算模拟 run={r.get('run_id')} 价值={p.get('value_per_conversion')} 成本={p.get('cost_per_contact')} "
        f"推荐 K={r.get('recommended_k')}/{r.get('n_population')}"
    ]
    rec = r.get("recommended") or {}
    if rec:
        out.append(
            f"推荐点期望转化={rec.get('expected_conversions')} 期望净收益={rec.get('expected_net')} "
            f"预算占用={rec.get('budget_used')}"
        )
    if r.get("disclaimer"):
        out.append(str(r["disclaimer"]))
    return out


def counterfactual_explain(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = []
    cf = r.get("counterfactual") or {}
    curve = r.get("curve") or {}
    if curve:
        out.append(
            f"单特征扰动 feature={curve.get('feature')} base={curve.get('base_value')} "
            f"proba 区间=[{min(curve.get('proba') or [0]):.4f},{max(curve.get('proba') or [0]):.4f}]"
        )
    if cf:
        out.append(
            f"反事实 base={cf.get('base_proba'):.4f} target={cf.get('target_proba')} "
            f"final={cf.get('final_proba'):.4f} achieved={cf.get('achieved')} steps={cf.get('n_steps')}"
        )
        for s in (cf.get("steps") or [])[:4]:
            out.append(f"步骤 {s.get('feature')}: {s.get('from')}→{s.get('to')} (proba={s.get('proba_after'):.4f})")
        out.append(str(cf.get("disclaimer") or ""))
    return out


def analysis_report(payload: dict[str, Any]) -> list[str]:
    r = payload.get("result") or {}
    out: list[str] = [
        f"报告《{r.get('title')}》：{r.get('n_sections_ok')}/{r.get('n_sections')} 节成功，"
        f"落盘 {r.get('report_path')}"
    ]
    for t in (r.get("tool_trace") or [])[:10]:
        out.append(f"章节[{t.get('section')}] 工具 {t.get('tool')} ok={t.get('ok')}")
    if r.get("disclaimer"):
        out.append(str(r["disclaimer"]))
    return out


def strategy_brief(payload: dict[str, Any]) -> list[str]:
    """综合摘要走兜底键名分支（与原 grounding else 行为一致）。"""
    r = payload.get("result") or {}
    return [f"工具 strategy_brief 已返回结果键: {list(r.keys())[:8]}"]
