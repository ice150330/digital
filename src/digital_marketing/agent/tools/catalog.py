"""只读分析工具实现（经产物门面）。

Stage 1：每个工具以 @tool(...) 一处声明（关键词/规划/facts/顺序/阶段），
REGISTRY 注册、plan_from_message 路由与 grounding 事实分派自动生效。
函数体保持历史行为不变。
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from digital_marketing.agent.tools import facts as F
from digital_marketing.agent.tools import tool
from digital_marketing.core.paths import resolve_under_root
from digital_marketing.services import artifacts
from digital_marketing.services.artifacts import ArtifactError


# ---------------------------------------------------------------------------
# 定制规划回调（需要 customer_id 上下文的工具）
# 关键词集合与原 local_runtime.plan_tools 逐字一致
# ---------------------------------------------------------------------------


def _hit(message: str, keywords: tuple[str, ...]) -> bool:
    msg = message.lower()
    return any(k in msg for k in keywords)


def _plan_predict(message: str, cid: int | None) -> dict[str, Any] | None:
    if cid is not None and _hit(message, ("预测", "proba", "概率", "解释客户", "shap", "局部", "客户")):
        return {"customer_id": cid}
    return None


def _plan_explain_customer(message: str, cid: int | None) -> dict[str, Any] | None:
    if cid is not None and _hit(message, ("预测", "proba", "概率", "解释客户", "shap", "局部")):
        return {"customer_id": cid, "top_k": 8}
    return None


def _plan_assign_cluster(message: str, cid: int | None) -> dict[str, Any] | None:
    if cid is not None and _hit(message, ("分群", "segment", "cluster", "簇")):
        return {"customer_id": cid}
    return None


def _plan_counterfactual(message: str, cid: int | None) -> dict[str, Any] | None:
    if cid is not None and _hit(
        message, ("反事实", "counterfactual", "如果", "what-if", "whatif", "怎么改", "如何提升概率")
    ):
        return {"customer_id": cid, "target_proba": 0.9}
    return None


# ---------------------------------------------------------------------------
# P0 工具
# ---------------------------------------------------------------------------


@tool(
    "get_dataset_profile",
    keywords=("画像", "概览", "样本", "overview", "数据规模", "多少行"),
    facts=F.dataset_profile,
    plan_order=18,
    stage="P0",
)
def get_dataset_profile() -> dict[str, Any]:
    ov = artifacts.get_overview()
    return {
        "n_rows": ov.get("n_rows"),
        "n_columns": ov.get("n_columns"),
        "positive_rate": ov.get("positive_rate"),
        "splits": ov.get("splits"),
        "notes": ov.get("notes"),
    }


@tool(
    "get_data_quality_issues",
    keywords=("质量", "quality", "issue", "异常", "不一致"),
    facts=F.data_quality_issues,
    plan_order=1,
    stage="P0",
)
def get_data_quality_issues() -> dict[str, Any]:
    ov = artifacts.get_overview()
    return {
        "issue_count": ov.get("issue_count"),
        "issues": ov.get("issues") or [],
        "email_inconsistent_count": ov.get("email_inconsistent_count"),
        "invalid_web_metrics_count": ov.get("invalid_web_metrics_count"),
    }


@tool(
    "conversion_by_dimension",
    keywords=("渠道", "channel", "转化率", "conversion"),
    base_kwargs={"dimension": "CampaignChannel"},
    facts=F.conversion_by_dimension,
    plan_order=2,
    stage="P0",
)
def conversion_by_dimension(dimension: str = "CampaignChannel") -> dict[str, Any]:
    """按维度汇总转化率（默认渠道）。"""
    clean = resolve_under_root("outputs/processed/clean.csv")
    if not clean.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少 clean.csv")
    df = pd.read_csv(clean)
    if dimension not in df.columns:
        raise ArtifactError("VALIDATION_ERROR", f"维度不存在: {dimension}")
    if "Conversion" not in df.columns:
        raise ArtifactError("ARTIFACT_MISSING", "缺少 Conversion 列")
    rows = []
    for key, g in df.groupby(dimension, dropna=False):
        rows.append(
            {
                "key": str(key),
                "n": int(len(g)),
                "conversion_rate": float(g["Conversion"].mean()),
            }
        )
    rows.sort(key=lambda r: r["conversion_rate"], reverse=True)
    return {"dimension": dimension, "items": rows}


@tool(
    "get_model_metrics",
    keywords=("指标", "metrics", "pr-auc", "prauc", "auc", "模型", "dummy"),
    facts=F.model_metrics,
    plan_order=3,
    stage="P0",
)
def get_model_metrics(run_id: str | None = None) -> dict[str, Any]:
    if run_id:
        return artifacts.get_metrics(run_id)
    items = artifacts.list_metrics()
    return {
        "primary_metric": "pr_auc",
        "default_run_id": artifacts.pick_default_run_id() if items else None,
        "items": items,
        "accuracy_note": "Accuracy 仅对照，请以 PR-AUC 为主并并列 Dummy",
    }


@tool(
    "get_feature_schema",
    keywords=("特征", "schema", "入模"),
    facts=F.feature_schema,
    plan_order=4,
    stage="P0",
)
def get_feature_schema() -> dict[str, Any]:
    return artifacts.meta_features()


@tool("predict_proba", plan=_plan_predict, facts=F.predict_proba, plan_order=6, stage="P0")
def predict_proba(customer_id: int | None = None, features: dict[str, Any] | None = None, run_id: str | None = None) -> dict[str, Any]:
    raw = artifacts.predict_row(customer_id=customer_id, features=features, run_id=run_id)
    return {
        "proba": raw["proba"],
        "label": raw["label"],
        "threshold": raw["threshold"],
        "run_id": raw["run_id"],
        "model_name": raw["model_name"],
        "customer_id": raw.get("customer_id"),
    }


@tool(
    "explain_global",
    keywords=("全局", "global shap", "全局解释", "重要特征"),
    facts=F.explain_global,
    plan_order=5,
    stage="P0",
)
def explain_global(run_id: str | None = None) -> dict[str, Any]:
    return artifacts.get_global_explain(run_id)


@tool("explain_customer", plan=_plan_explain_customer, facts=F.explain_customer, plan_order=7, stage="P0")
def explain_customer(
    customer_id: int | None = None,
    features: dict[str, Any] | None = None,
    run_id: str | None = None,
    top_k: int = 8,
) -> dict[str, Any]:
    return artifacts.explain_customer(
        customer_id=customer_id,
        features=features,
        run_id=run_id,
        top_k=top_k,
    )


# ---------------------------------------------------------------------------
# P1 工具
# ---------------------------------------------------------------------------


@tool(
    "segment_summary",
    keywords=("分群", "segment", "cluster", "簇"),
    facts=F.segment_summary,
    plan_order=8,
    stage="P1",
)
def segment_summary() -> dict[str, Any]:
    path = resolve_under_root("outputs/segments/summary.json")
    if not path.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少分群产物，请运行 python scripts/04_train_cluster.py")
    return artifacts.load_json(path)


@tool("assign_cluster", plan=_plan_assign_cluster, facts=F.assign_cluster, plan_order=9, stage="P1")
def assign_cluster(customer_id: int | None = None, features: dict[str, Any] | None = None) -> dict[str, Any]:
    from digital_marketing.segment.assign import assign_one

    return assign_one(customer_id=customer_id, features=features)


@tool(
    "top_association_rules",
    keywords=("规则", "association", "lift", "关联"),
    base_kwargs={"min_lift": 1.0, "limit": 10},
    facts=F.top_association_rules,
    plan_order=10,
    stage="P1",
)
def top_association_rules(min_lift: float = 1.0, limit: int = 20) -> dict[str, Any]:
    path = resolve_under_root("outputs/rules/top_rules.json")
    if not path.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少关联规则产物，请运行 python scripts/05_mine_rules.py")
    data = artifacts.load_json(path)
    rules = data.get("rules") or data.get("items") or []
    filtered = [r for r in rules if float(r.get("lift") or 0) >= min_lift]
    filtered = filtered[:limit]
    return {
        "n_total": len(rules),
        "n_returned": len(filtered),
        "min_lift": min_lift,
        "disclaimer": data.get("disclaimer") or "关联规则表达相关而非因果",
        "rules": filtered,
    }


@tool(
    "strategy_brief",
    keywords=("策略", "brief", "综合", "建议摘要"),
    facts=F.strategy_brief,
    plan_order=17,
    stage="P1",
)
def strategy_brief() -> dict[str, Any]:
    """综合只读摘要：指标 + 可选分群/规则；不含因果断言。"""
    brief: dict[str, Any] = {
        "disclaimer": "本摘要仅综合分析产物，不构成因果或投放保证。",
        "primary_metric": "pr_auc",
    }
    try:
        brief["dataset"] = get_dataset_profile()
    except Exception as e:  # noqa: BLE001
        brief["dataset_error"] = str(e)
    try:
        brief["metrics"] = get_model_metrics()
    except Exception as e:  # noqa: BLE001
        brief["metrics_error"] = str(e)
    try:
        brief["segments"] = segment_summary()
    except Exception as e:  # noqa: BLE001
        brief["segments_note"] = str(e)
    try:
        brief["rules_top"] = top_association_rules(min_lift=1.1, limit=5)
    except Exception as e:  # noqa: BLE001
        brief["rules_note"] = str(e)
    return brief


# ---------------------------------------------------------------------------
# 阶段9 新增工具（增强评估 / 模拟 / 反事实）
# ---------------------------------------------------------------------------


@tool(
    "compare_experiments",
    keywords=("实验对比", "对比实验", "compare", "消融", "ablation", "stacking", "集成", "所有模型", "全量"),
    facts=F.compare_experiments,
    plan_order=11,
    stage="阶段9",
)
def compare_experiments() -> dict[str, Any]:
    """实验对比：全量 leaderboard（CV/CI/校准/消融标记）。"""
    items = artifacts.list_metrics()
    default_run = None
    try:
        default_run = artifacts.pick_default_run_id()
    except ArtifactError:
        pass
    return {
        "n_runs": len(items),
        "default_run_id": default_run,
        "primary_metric": "pr_auc",
        "items": items,
        "note": "E5 为含 ConversionRate 的泄漏消融、E6 为去质量 flag 消融，二者不参选默认 run；"
        "cv_pr_auc_mean/std 为 train 5-fold；pr_auc_ci_* 为 test bootstrap 95% CI",
    }


@tool(
    "get_calibration_summary",
    keywords=("校准", "calibrat", "brier", "ece"),
    facts=F.calibration_summary,
    plan_order=12,
    stage="阶段9",
)
def get_calibration_summary(run_id: str | None = None) -> dict[str, Any]:
    """校准摘要（默认取 E8 校准 run）。"""
    rid = run_id or "E8_lightgbm_calibrated"
    data = artifacts.get_calibration(rid)
    return {
        "run_id": data.get("run_id", rid),
        "method": data.get("method"),
        "brier_before": (data.get("before") or {}).get("brier"),
        "brier_after": (data.get("after") or {}).get("brier"),
        "ece_before": (data.get("before") or {}).get("ece"),
        "ece_after": (data.get("after") or {}).get("ece"),
        "note": data.get("note"),
    }


@tool(
    "get_lift_table",
    keywords=("升降", "增益", "gains", "十分位", "decile"),
    facts=F.lift_table,
    plan_order=13,
    stage="阶段9",
)
def get_lift_table(run_id: str | None = None) -> dict[str, Any]:
    """lift/gains 十分位表。"""
    return artifacts.get_lift(run_id)


@tool(
    "simulate_budget",
    keywords=("预算", "budget", "触达", "名单", "roi", "收益模拟", "模拟"),
    facts=F.simulate_budget,
    plan_order=14,
    stage="阶段9",
)
def simulate_budget(
    budget: float | None = None,
    value_per_conversion: float = 10.0,
    cost_per_contact: float = 4.0,
    run_id: str | None = None,
) -> dict[str, Any]:
    """预算分配模拟（期望值口径，非因果）。"""
    raw = artifacts.simulate_budget(
        budget=budget,
        value_per_conversion=value_per_conversion,
        cost_per_contact=cost_per_contact,
        run_id=run_id,
        export=False,
    )
    # Agent 场景压缩曲线点，避免超长上下文
    if len(raw.get("curve") or []) > 12:
        raw["curve"] = raw["curve"][::2]
        raw["curve_note"] = "曲线已抽稀展示"
    return raw


@tool("counterfactual_explain", plan=_plan_counterfactual, facts=F.counterfactual_explain, plan_order=16, stage="阶段9")
def counterfactual_explain(
    customer_id: int | None = None,
    feature: str | None = None,
    target_proba: float | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """反事实（模型行为口径）：单特征扰动曲线 + 可选达标路径。"""
    if customer_id is None:
        raise ArtifactError("VALIDATION_ERROR", "counterfactual_explain 需要 customer_id")
    return artifacts.counterfactual_customer(
        customer_id=customer_id,
        feature=feature,
        target_proba=target_proba,
        run_id=run_id,
        grid_size=15,
        max_steps=6,
    )


@tool(
    "generate_analysis_report",
    keywords=("报告", "report", "生成分析", "论文素材", "汇总报告"),
    facts=F.analysis_report,
    plan_order=15,
    stage="阶段9",
)
def generate_analysis_report(
    title: str = "数字营销转化分析报告",
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """一键生成分析报告（编排只读工具 → markdown 落盘 outputs/reports/）。"""
    from digital_marketing.agent.report import generate_analysis_report as _gen

    return _gen(title=title, sections=sections)


# ---------------------------------------------------------------------------
# Stage 4：声明式图表工具（chart-spec v1.0）
# 宿主从真实数据源计算数据 → 纯 JSON spec；前端 ChartCard 映射渲染，
# 色板单一真相在前端；LLM/Pi 永不产数字、永不产 spec（§9.1 host-executed）。
# ---------------------------------------------------------------------------

CHART_SPEC_VERSION = "1.0"
CHART_TYPES = ("bar", "line", "pie", "scatter", "heatmap", "funnel")
CHART_DATASETS = (
    "conversion_by_channel",
    "conversion_by_type",
    "leaderboard_pr",
    "age_hist",
    "income_hist",
    "adspend_hist",
    "segment_sizes",
    "lift_deciles",
    "global_shap_top",
)


def _chart_facts(payload: dict[str, Any]) -> list[str]:
    """图表事实只述存在性，不重复数字（数字在图里，避免叙述与图不一致）。"""
    r = payload.get("result") or {}
    src = (r.get("source") or {}).get("ref")
    return [f"已生成《{r.get('title')}》图表（chart_type={r.get('chart_type')}, 数据源={src}）"]


def _plan_render_chart(message: str, cid: int | None) -> dict[str, Any] | None:
    msg = message.lower()
    if not any(
        k in msg
        for k in (
            "画图", "画个", "画一", "图表", "可视化", "chart", "plot",
            "柱状图", "饼图", "曲线图", "对比图", "分布图", "热力图", "条形图", "折线图",
        )
    ):
        return None
    if any(k in msg for k in ("渠道", "channel")):
        return {"chart_type": "bar", "dataset": "conversion_by_channel"}
    if any(k in msg for k in ("活动类型", "类型", "campaign type")):
        return {"chart_type": "bar", "dataset": "conversion_by_type"}
    if any(k in msg for k in ("实验", "leaderboard", "pr-auc", "模型对比", "排行", "榜单")):
        return {"chart_type": "bar", "dataset": "leaderboard_pr"}
    if "年龄" in msg:
        return {"chart_type": "bar", "dataset": "age_hist"}
    if "收入" in msg:
        return {"chart_type": "bar", "dataset": "income_hist"}
    if any(k in msg for k in ("支出", "adspend", "广告费", "花费")):
        return {"chart_type": "bar", "dataset": "adspend_hist"}
    if any(k in msg for k in ("分群", "簇", "segment", "占比")):
        return {"chart_type": "pie", "dataset": "segment_sizes"}
    if any(k in msg for k in ("lift", "升降", "十分位", "decile")):
        return {"chart_type": "line", "dataset": "lift_deciles"}
    if any(k in msg for k in ("shap", "特征重要", "归因", "全局解释")):
        return {"chart_type": "bar", "dataset": "global_shap_top"}
    return {"chart_type": "bar", "dataset": "conversion_by_channel"}


def _spec(
    chart_type: str,
    title: str,
    categories: list[str],
    series: list[dict[str, Any]],
    value_format: str,
    axis: dict[str, str],
    caliber: str,
    source: dict[str, Any],
    disclaimer: str | None = None,
) -> dict[str, Any]:
    return {
        "spec_version": CHART_SPEC_VERSION,
        "chart_type": chart_type,
        "title": title,
        "categories": categories,
        "series": series,
        "value_format": value_format,
        "axis": axis,
        "caliber": caliber,
        "source": source,
        "disclaimer": disclaimer,
    }


@tool(
    "render_chart",
    plan=_plan_render_chart,
    facts=_chart_facts,
    plan_order=19,
    stage="Stage4",
)
def render_chart(
    chart_type: str = "bar",
    dataset: str = "conversion_by_channel",
    limit: int = 10,
    title: str | None = None,
) -> dict[str, Any]:
    """生成声明式图表 spec（纯 JSON）：宿主计算真实数据，前端 ChartCard 渲染。"""
    if chart_type not in CHART_TYPES:
        raise ArtifactError("VALIDATION_ERROR", f"chart_type 必须是 {list(CHART_TYPES)} 之一: {chart_type}")
    if dataset not in CHART_DATASETS:
        raise ArtifactError("VALIDATION_ERROR", f"dataset 必须是 {list(CHART_DATASETS)} 之一: {dataset}")
    limit = max(1, min(int(limit), 50))

    if dataset in ("conversion_by_channel", "conversion_by_type"):
        dim = "CampaignChannel" if dataset == "conversion_by_channel" else "CampaignType"
        r = conversion_by_dimension(dimension=dim)
        items = (r.get("items") or [])[:limit]
        return _spec(
            chart_type,
            title or f"{'渠道' if dim == 'CampaignChannel' else '活动类型'}转化率",
            [str(it.get("key")) for it in items],
            [{"name": "转化率", "values": [float(it.get("conversion_rate") or 0) for it in items]}],
            "percent2",
            {"x_name": "渠道" if dim == "CampaignChannel" else "活动类型", "y_name": "转化率"},
            f"横截面：campaigns 全表按 {dim} 分组独立计数，组间差异为相关关系",
            {"kind": "artifact", "ref": "clean.csv", "run_id": None},
            disclaimer="维度间差异为相关关系，非因果",
        )

    if dataset == "leaderboard_pr":
        items = (artifacts.list_metrics() or [])[:limit]
        return _spec(
            chart_type,
            title or "实验矩阵 PR-AUC 对比",
            [str(it.get("run_id")) for it in items],
            [{"name": "PR-AUC", "values": [float(it.get("pr_auc") or 0) for it in items]}],
            "float4",
            {"x_name": "实验 run", "y_name": "PR-AUC"},
            "test 集一次评估；CI 重叠的 run 之间不宣称更优；E5/E6 为消融 run",
            {"kind": "artifact", "ref": "leaderboard.json", "run_id": None},
        )

    if dataset in ("age_hist", "income_hist", "adspend_hist"):
        from digital_marketing.services.dashboard import get_dashboard

        col = {"age_hist": "age", "income_hist": "income", "adspend_hist": "ad_spend"}[dataset]
        dash = get_dashboard()
        bins = (dash.get("histograms") or {}).get(col) or []
        return _spec(
            chart_type,
            title or f"{col} 分布",
            [f"{b['lo']:.0f}–{b['hi']:.0f}" for b in bins],
            [{"name": "样本数", "values": [int(b["count"]) for b in bins]}],
            "int",
            {"x_name": col, "y_name": "样本数"},
            dash.get("caliber") or "横截面统计",
            {"kind": "sqlite", "ref": "campaigns", "run_id": None},
        )

    if dataset == "segment_sizes":
        r = segment_summary()
        clusters = (r.get("clusters") or [])[:limit]
        names = [str(c.get("auto_name") or f"簇{c.get('cluster_id')}") for c in clusters]
        return _spec(
            chart_type,
            title or "分群规模占比",
            names,
            [{"name": "样本数", "values": [int(c.get("n") or 0) for c in clusters]}],
            "int",
            {"x_name": "分群", "y_name": "样本数"},
            "分群训练不含 Conversion；簇规模与事后转化率均为横截面统计",
            {"kind": "artifact", "ref": "segments/summary.json", "run_id": None},
            disclaimer="分群为无监督结果，画像不构成因果",
        )

    if dataset == "lift_deciles":
        r = artifacts.get_lift()
        deciles = (r.get("lift_deciles") or [])[:limit]
        return _spec(
            chart_type,
            title or "营销升降表（十分位）",
            [str(d.get("decile")) for d in deciles],
            [
                {"name": "累计捕获率", "values": [float(d.get("capture_rate") or 0) for d in deciles]},
                {"name": "lift", "values": [float(d.get("lift") or 0) for d in deciles]},
            ],
            "float4",
            {"x_name": "十分位（按预测概率降序）", "y_name": "捕获率 / lift"},
            "test 集十分位统计；lift 相对全量基准",
            {"kind": "artifact", "ref": "lift_deciles", "run_id": r.get("run_id")},
        )

    # global_shap_top
    r = artifacts.get_global_explain()
    feats = (r.get("top_features") or [])[:limit]
    return _spec(
        chart_type,
        title or "全局特征重要性 Top",
        [str(f.get("name")) for f in feats],
        [{"name": "mean |SHAP|", "values": [float(f.get("mean_abs_shap") or 0) for f in feats]}],
        "float4",
        {"x_name": "特征", "y_name": "mean |SHAP|"},
        f"模型贡献方向（method={r.get('method')}），非严格因果",
        {"kind": "artifact", "ref": "explain/global", "run_id": r.get("run_id")},
        disclaimer="SHAP 为模型归因，不构成因果",
    )
