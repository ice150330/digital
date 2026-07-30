"""Agent 工具白名单注册。"""

from __future__ import annotations

from typing import Any, Callable

from digital_marketing.agent.tools import catalog

ToolFn = Callable[..., dict[str, Any]]

REGISTRY: dict[str, ToolFn] = {
    "get_dataset_profile": catalog.get_dataset_profile,
    "get_data_quality_issues": catalog.get_data_quality_issues,
    "conversion_by_dimension": catalog.conversion_by_dimension,
    "get_model_metrics": catalog.get_model_metrics,
    "get_feature_schema": catalog.get_feature_schema,
    "predict_proba": catalog.predict_proba,
    "explain_global": catalog.explain_global,
    "explain_customer": catalog.explain_customer,
    "segment_summary": catalog.segment_summary,
    "assign_cluster": catalog.assign_cluster,
    "top_association_rules": catalog.top_association_rules,
    "strategy_brief": catalog.strategy_brief,
}


def list_tools() -> list[str]:
    return sorted(REGISTRY.keys())


def run_tool(name: str, **kwargs: Any) -> dict[str, Any]:
    if name not in REGISTRY:
        return {"ok": False, "error": f"未知工具: {name}", "tool": name}
    try:
        result = REGISTRY[name](**kwargs)
        return {"ok": True, "tool": name, "result": result}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "tool": name, "error": str(e)}
