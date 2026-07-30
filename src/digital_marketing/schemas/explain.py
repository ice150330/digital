"""解释 DTO。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ShapFeature(BaseModel):
    name: str
    feature_value: Any | None = None
    shap_value: float | None = None
    mean_abs_shap: float | None = None


class GlobalExplainData(BaseModel):
    run_id: str
    method: str
    n_samples: int | None = None
    top_features: list[dict[str, Any]] = Field(default_factory=list)


class CustomerExplainRequest(BaseModel):
    customer_id: int | None = None
    features: dict[str, Any] | None = None
    run_id: str | None = None
    top_k: int = 10


class CustomerExplainData(BaseModel):
    run_id: str
    model_name: str | None = None
    method: str
    proba: float | None = None
    label: int | None = None
    threshold: float | None = None
    customer_id: int | None = None
    top_features: list[dict[str, Any]] = Field(default_factory=list)
