"""分群 DTO。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SegmentsData(BaseModel):
    method: str | None = None
    n_clusters: int | None = None
    n_samples: int | None = None
    disclaimer: str | None = None
    clusters: list[dict[str, Any]] = Field(default_factory=list)
    feature_columns: list[str] = Field(default_factory=list)
    label_excluded: bool | None = True


class AssignRequest(BaseModel):
    customer_id: int | None = None
    features: dict[str, Any] | None = None


class AssignData(BaseModel):
    cluster_id: int
    distance: float | None = None
    customer_id: int | None = None
    cluster: dict[str, Any] | None = None
    disclaimer: str | None = None
