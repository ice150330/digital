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


# ---------------------------------------------------------------------------
# Stage 3：大屏 / L1 描述性聚合
# ---------------------------------------------------------------------------


class DashboardKpis(BaseModel):
    n_rows: int
    positive_rate: float
    total_ad_spend: float
    avg_ctr: float
    avg_pages_per_visit: float
    repurchase_rate: float


class FunnelStage(BaseModel):
    stage: str
    label: str
    count: int
    rate_vs_total: float


class HistBin(BaseModel):
    lo: float
    hi: float
    count: int


class ChannelFunnel(BaseModel):
    """渠道级转化漏斗（桑基主图用）：每渠道 × 阶段计数，横截面独立计数，非嵌套。"""

    channel: str
    n: int
    email_opened: int = 0
    email_clicked: int = 0
    visited: int = 0
    deep_visited: int = 0
    converted: int = 0


class DashboardData(BaseModel):
    """大屏聚合数据；caliber 为口径真相源（横截面、伪漏斗非 cohort、时序不可做）。"""

    kpis: DashboardKpis
    funnel: list[FunnelStage]
    channel_funnel: list[ChannelFunnel] = Field(default_factory=list)
    histograms: dict[str, list[HistBin]]
    caliber: str
    source: str
    notes: dict[str, Any] = Field(default_factory=dict)


class CrossCell(BaseModel):
    row: str
    col: str
    n: int
    conversion_rate: float


class CrossTotal(BaseModel):
    key: str
    n: int
    conversion_rate: float


class CrossMatrixData(BaseModel):
    row_dim: str
    col_dim: str
    cells: list[CrossCell]
    row_totals: list[CrossTotal]
    col_totals: list[CrossTotal]
    caliber: str


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
