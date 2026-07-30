"""模拟器 DTO：预算分配。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BudgetSimulateRequest(BaseModel):
    budget: float | None = Field(default=None, description="总预算；缺省则全量扫描")
    value_per_conversion: float = Field(default=10.0, gt=0)
    cost_per_contact: float = Field(default=4.0, gt=0)
    run_id: str | None = None
    export: bool = False
    n_points: int = Field(default=25, ge=5, le=100)


class BudgetSimulateData(BaseModel):
    run_id: str
    params: dict[str, Any]
    n_population: int
    curve: list[dict[str, Any]]
    recommended_k: int
    recommended: dict[str, Any] | None = None
    calibrated: bool = False
    top_list: list[dict[str, Any]] = Field(default_factory=list, description="Top 名单预览（≤50 条）")
    export_path: str | None = None
    disclaimer: str
