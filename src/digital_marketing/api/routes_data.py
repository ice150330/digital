"""数据概览与特征 meta。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from digital_marketing.api.errors import from_artifact_error
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.data import FeatureMetaData, OverviewData
from digital_marketing.services import artifacts
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


@router.get("/meta/features", response_model=Envelope[FeatureMetaData])
def meta_features(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.meta_features()
        data = FeatureMetaData.model_validate(raw)
        return Envelope[FeatureMetaData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)
