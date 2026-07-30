"""阶段9 增强分析 DTO：曲线 / 校准 / lift / 阈值扫描 / PDP / 反事实。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CurvesData(BaseModel):
    run_id: str
    pr_auc: float | None = None
    roc_auc: float | None = None
    ci: dict[str, Any] = Field(default_factory=dict)
    cv: dict[str, Any] = Field(default_factory=dict)
    pr_curve: dict[str, Any]
    roc_curve: dict[str, Any]


class LiftData(BaseModel):
    run_id: str
    lift_deciles: list[dict[str, Any]]
    note: str | None = None


class ThresholdScanData(BaseModel):
    run_id: str
    cost_fp: float
    cost_fn: float
    cost_note: str | None = None
    rows: list[dict[str, Any]]
    best_by_cost: dict[str, Any] | None = None
    current_threshold: float | None = None


class PdpData(BaseModel):
    run_id: str
    feature: str | None = None
    grid: list[float] | None = None
    pdp: list[float] | None = None
    ice: list[dict[str, Any]] | None = None
    features: dict[str, Any] | None = None
    disclaimer: str | None = None


class CounterfactualRequest(BaseModel):
    customer_id: int | None = None
    features: dict[str, Any] | None = None
    feature: str | None = None
    target_proba: float | None = None
    run_id: str | None = None
    grid_size: int = 25
    max_steps: int = 8


class CounterfactualData(BaseModel):
    run_id: str
    customer_id: int | None = None
    curve: dict[str, Any] | None = None
    counterfactual: dict[str, Any] | None = None
