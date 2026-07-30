"""关联规则 DTO。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RulesData(BaseModel):
    method: str | None = None
    n_rules: int | None = None
    min_lift: float | None = None
    disclaimer: str = "关联规则表达相关而非因果"
    rules: list[dict[str, Any]] = Field(default_factory=list)
