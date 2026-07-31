"""数据概览、特征 meta 与大屏描述性聚合（Stage 3）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from digital_marketing.api.errors import from_artifact_error
from digital_marketing.data.db import get_db
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.data import (
    CrossMatrixData,
    DashboardData,
    FeatureMetaData,
    OverviewData,
)
from digital_marketing.services import artifacts, dashboard
from digital_marketing.services.artifacts import ArtifactError

router = APIRouter(tags=["data"])


@router.get("/data/overview", response_model=Envelope[OverviewData])
def data_overview(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.get_overview()
        data = OverviewData.model_validate(raw)
        return Envelope[OverviewData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/data/dashboard", response_model=Envelope[DashboardData])
def data_dashboard(request: Request, db: Session = Depends(get_db)):
    """大屏聚合：KPI + 伪漏斗 + 分布直方图（横截面口径，见 caliber）。"""
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = dashboard.get_dashboard(db)
        data = DashboardData.model_validate(raw)
        return Envelope[DashboardData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/data/cross-matrix", response_model=Envelope[CrossMatrixData])
def data_cross_matrix(
    request: Request,
    db: Session = Depends(get_db),
    row_dim: str = Query(default="campaign_channel"),
    col_dim: str = Query(default="campaign_type"),
):
    """二维交叉转化率矩阵（维度白名单：campaign_channel/campaign_type/gender）。"""
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = dashboard.get_cross_matrix(row_dim, col_dim, db)
        data = CrossMatrixData.model_validate(raw)
        return Envelope[CrossMatrixData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/meta/features", response_model=Envelope[FeatureMetaData])
def meta_features(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.meta_features()
        data = FeatureMetaData.model_validate(raw)
        return Envelope[FeatureMetaData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)
