"""只读分析工具实现（经产物门面）。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from digital_marketing.core.paths import resolve_under_root
from digital_marketing.services import artifacts
from digital_marketing.services.artifacts import ArtifactError


def get_dataset_profile() -> dict[str, Any]:
    ov = artifacts.get_overview()
    return {
        "n_rows": ov.get("n_rows"),
        "n_columns": ov.get("n_columns"),
        "positive_rate": ov.get("positive_rate"),
        "splits": ov.get("splits"),
        "notes": ov.get("notes"),
    }


def get_data_quality_issues() -> dict[str, Any]:
    ov = artifacts.get_overview()
    return {
        "issue_count": ov.get("issue_count"),
        "issues": ov.get("issues") or [],
        "email_inconsistent_count": ov.get("email_inconsistent_count"),
        "invalid_web_metrics_count": ov.get("invalid_web_metrics_count"),
    }


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


def get_feature_schema() -> dict[str, Any]:
    return artifacts.meta_features()


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


def explain_global(run_id: str | None = None) -> dict[str, Any]:
    return artifacts.get_global_explain(run_id)


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


def segment_summary() -> dict[str, Any]:
    path = resolve_under_root("outputs/segments/summary.json")
    if not path.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少分群产物，请运行 python scripts/04_train_cluster.py")
    return artifacts.load_json(path)


def assign_cluster(customer_id: int | None = None, features: dict[str, Any] | None = None) -> dict[str, Any]:
    from digital_marketing.segment.assign import assign_one

    return assign_one(customer_id=customer_id, features=features)


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
