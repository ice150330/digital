"""数据 / 特征 meta DTO。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChannelStat(BaseModel):
    channel: str
    n: int
    conversion_rate: float


class QualityIssue(BaseModel):
    code: str
    count: int | None = None
    message: str | None = None
    column: str | None = None


class OverviewData(BaseModel):
    n_rows: int | None = None
    n_columns: int | None = None
    positive_rate: float | None = None
    issues: list[dict[str, Any]] = Field(default_factory=list)
    issue_count: int = 0
    channel_stats: list[dict[str, Any]] = Field(default_factory=list)
    email_inconsistent_count: int | None = None
    invalid_web_metrics_count: int | None = None
    splits: dict[str, Any] | None = None
    notes: dict[str, Any] = Field(default_factory=dict)


class FeatureMetaData(BaseModel):
    target: str
    feature_columns_raw: list[str]
    feature_names_out: list[str] = Field(default_factory=list)
    drop_features: list[str] = Field(default_factory=list)
    never_features: list[str] = Field(default_factory=list)
    categorical_features: list[str] = Field(default_factory=list)
    numeric_features: list[str] = Field(default_factory=list)
    flag_features: list[str] = Field(default_factory=list)
    sample_defaults: dict[str, Any] = Field(default_factory=dict)
