"""模型指标与预测 DTO。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MetricRow(BaseModel):
    run_id: str
    exp_id: str | None = None
    model_name: str | None = None
    pr_auc: float | None = None
    roc_auc: float | None = None
    f1: float | None = None
    accuracy: float | None = None
    threshold: float | None = None


class MetricsListData(BaseModel):
    items: list[dict[str, Any]]
    primary_metric: str = "pr_auc"
    accuracy_note: str = "Accuracy 仅对照，请以 PR-AUC 为主并并列 Dummy"


class PredictRequest(BaseModel):
    customer_id: int | None = None
    features: dict[str, Any] | None = None
    run_id: str | None = None


class PredictData(BaseModel):
    proba: float
    label: int
    threshold: float
    run_id: str
    model_name: str
    customer_id: int | None = None


class BatchPredictRequest(BaseModel):
    customer_ids: list[int] | None = None
    rows: list[dict[str, Any]] | None = None
    run_id: str | None = None


class BatchPredictData(BaseModel):
    run_id: str
    model_name: str
    threshold: float
    n_requested: int
    n_ok: int
    n_error: int
    items: list[PredictData] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    max_items: int = 200
    note: str | None = None
