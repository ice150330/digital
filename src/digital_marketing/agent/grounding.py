"""Agent 输出契约：五段字段 + tool_trace，禁止无工具编造数字。"""

from __future__ import annotations

from typing import Any


REQUIRED_SECTIONS = (
    "observed_facts",
    "inferences",
    "recommendations",
    "open_questions",
    "tool_trace",
)


def empty_result(*, runtime: str, session_id: str, message: str = "") -> dict[str, Any]:
    return {
        "runtime": runtime,
        "session_id": session_id,
        "observed_facts": [],
        "inferences": [],
        "recommendations": [],
        "open_questions": [message] if message else [],
        "tool_trace": [],
        "reply": message or "暂无工具结果。",
    }


def build_structured_reply(
    *,
    runtime: str,
    session_id: str,
    tool_trace: list[dict[str, Any]],
    facts: list[str],
    inferences: list[str],
    recommendations: list[str],
    open_questions: list[str] | None = None,
    reply: str | None = None,
) -> dict[str, Any]:
    """组装契约化响应。"""
    body = {
        "runtime": runtime,
        "session_id": session_id,
        "observed_facts": facts,
        "inferences": inferences,
        "recommendations": recommendations,
        "open_questions": open_questions or [],
        "tool_trace": tool_trace,
        "reply": reply
        or _compose_reply(facts, inferences, recommendations, open_questions or []),
    }
    for k in REQUIRED_SECTIONS:
        if k not in body:
            body[k] = [] if k != "tool_trace" else []
    return body


def _compose_reply(
    facts: list[str],
    inferences: list[str],
    recommendations: list[str],
    open_questions: list[str],
) -> str:
    parts: list[str] = []
    if facts:
        parts.append("【观察事实】\n" + "\n".join(f"- {x}" for x in facts))
    if inferences:
        parts.append("【推断】\n" + "\n".join(f"- {x}" for x in inferences))
    if recommendations:
        parts.append("【建议】\n" + "\n".join(f"- {x}" for x in recommendations))
    if open_questions:
        parts.append("【待确认】\n" + "\n".join(f"- {x}" for x in open_questions))
    if not parts:
        return "已执行工具，但未提炼出可展示事实。请查看 tool_trace。"
    return "\n\n".join(parts)


def facts_from_tool(tool: str, payload: dict[str, Any]) -> list[str]:
    """从工具结果抽取可引用事实字符串（仅基于结果，不编造）。"""
    if not payload.get("ok"):
        return [f"工具 {tool} 失败: {payload.get('error')}"]
    r = payload.get("result") or {}
    out: list[str] = []
    if tool == "get_dataset_profile":
        if r.get("n_rows") is not None:
            out.append(f"样本量 n_rows={r['n_rows']}")
        if r.get("positive_rate") is not None:
            out.append(f"正类占比 positive_rate={float(r['positive_rate']):.4f}")
    elif tool == "get_data_quality_issues":
        out.append(f"质量 issue 条数={r.get('issue_count')}")
        for it in (r.get("issues") or [])[:5]:
            out.append(f"issue {it.get('code')}: count={it.get('count')}")
    elif tool == "conversion_by_dimension":
        dim = r.get("dimension")
        for it in (r.get("items") or [])[:6]:
            out.append(
                f"{dim}={it.get('key')}: n={it.get('n')}, conversion_rate={float(it.get('conversion_rate') or 0):.4f}"
            )
    elif tool == "get_model_metrics":
        items = r.get("items") or ([r] if r.get("run_id") else [])
        for it in items[:5]:
            out.append(
                f"run={it.get('run_id')} PR-AUC={it.get('pr_auc')} ROC-AUC={it.get('roc_auc')} "
                f"Accuracy(对照)={it.get('accuracy')}"
            )
        if r.get("accuracy_note"):
            out.append(str(r["accuracy_note"]))
    elif tool == "get_feature_schema":
        cols = r.get("feature_columns_raw") or []
        out.append(f"入模原始特征数={len(cols)}；永不入模={r.get('never_features')}")
    elif tool == "predict_proba":
        out.append(
            f"proba={r.get('proba')}, label={r.get('label')}, threshold={r.get('threshold')}, run_id={r.get('run_id')}"
        )
    elif tool == "explain_global":
        out.append(f"全局解释 method={r.get('method')} run_id={r.get('run_id')}")
        for f in (r.get("top_features") or [])[:5]:
            out.append(f"特征 {f.get('name')} mean_abs={f.get('mean_abs_shap')}")
    elif tool == "explain_customer":
        out.append(
            f"客户解释 method={r.get('method')} proba={r.get('proba')} run_id={r.get('run_id')}"
        )
        for f in (r.get("top_features") or [])[:5]:
            out.append(f"{f.get('name')} shap={f.get('shap_value')}")
    elif tool == "segment_summary":
        out.append(f"分群 k={r.get('n_clusters')} method={r.get('method')}")
        for c in (r.get("clusters") or [])[:8]:
            out.append(
                f"簇 {c.get('cluster_id')}: n={c.get('n')}, conversion_rate(事后)={c.get('conversion_rate')}"
            )
    elif tool == "assign_cluster":
        out.append(f"分配簇 cluster_id={r.get('cluster_id')} distance={r.get('distance')}")
    elif tool == "top_association_rules":
        out.append(r.get("disclaimer") or "规则相关非因果")
        for rule in (r.get("rules") or [])[:5]:
            out.append(
                f"{rule.get('antecedents')} => {rule.get('consequents')} "
                f"support={rule.get('support')} conf={rule.get('confidence')} lift={rule.get('lift')}"
            )
    elif tool == "compare_experiments":
        out.append(f"实验数 n={r.get('n_runs')}，默认 run={r.get('default_run_id')}")
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
    elif tool == "get_calibration_summary":
        out.append(
            f"校准 run={r.get('run_id')} method={r.get('method')} "
            f"brier {r.get('brier_before')}→{r.get('brier_after')} "
            f"ece {r.get('ece_before')}→{r.get('ece_after')}"
        )
    elif tool == "get_lift_table":
        out.append(f"lift 表 run={r.get('run_id')}")
        for d in (r.get("lift_deciles") or [])[:3]:
            out.append(
                f"十分位 {d.get('decile')}: n={d.get('n')}, 累计捕获率={d.get('capture_rate'):.4f}, lift={d.get('lift'):.4f}"
            )
    elif tool == "simulate_budget":
        p = r.get("params") or {}
        out.append(
            f"预算模拟 run={r.get('run_id')} 价值={p.get('value_per_conversion')} 成本={p.get('cost_per_contact')} "
            f"推荐 K={r.get('recommended_k')}/{r.get('n_population')}"
        )
        rec = r.get("recommended") or {}
        if rec:
            out.append(
                f"推荐点期望转化={rec.get('expected_conversions')} 期望净收益={rec.get('expected_net')} "
                f"预算占用={rec.get('budget_used')}"
            )
        if r.get("disclaimer"):
            out.append(str(r["disclaimer"]))
    elif tool == "counterfactual_explain":
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
    elif tool == "generate_analysis_report":
        out.append(
            f"报告《{r.get('title')}》：{r.get('n_sections_ok')}/{r.get('n_sections')} 节成功，"
            f"落盘 {r.get('report_path')}"
        )
        for t in (r.get("tool_trace") or [])[:10]:
            out.append(f"章节[{t.get('section')}] 工具 {t.get('tool')} ok={t.get('ok')}")
        if r.get("disclaimer"):
            out.append(str(r["disclaimer"]))
    else:
        out.append(f"工具 {tool} 已返回结果键: {list(r.keys())[:8]}")
    return out
