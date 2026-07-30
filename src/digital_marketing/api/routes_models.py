"""模型指标与预测。"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from digital_marketing.api.errors import from_artifact_error
from digital_marketing.schemas.advanced import CurvesData, LiftData, ThresholdScanData
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.models import (
    BatchPredictData,
    BatchPredictRequest,
    MetricsListData,
    PredictData,
    PredictRequest,
)
from digital_marketing.services import artifacts
from digital_marketing.services.artifacts import ArtifactError

router = APIRouter(tags=["models"])


@router.get("/models/metrics", response_model=Envelope[MetricsListData])
def models_metrics(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        items = artifacts.list_metrics()
        data = MetricsListData(items=items)
        return Envelope[MetricsListData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/models/metrics/{run_id}", response_model=Envelope[dict])
def models_metrics_one(run_id: str, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        data = artifacts.get_metrics(run_id)
        return Envelope[dict](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.post("/models/predict", response_model=Envelope[PredictData])
def models_predict(body: PredictRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.predict_row(
            customer_id=body.customer_id,
            features=body.features,
            run_id=body.run_id,
        )
        data = PredictData(
            proba=raw["proba"],
            label=raw["label"],
            threshold=raw["threshold"],
            run_id=raw["run_id"],
            model_name=raw["model_name"],
            customer_id=raw.get("customer_id"),
        )
        return Envelope[PredictData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.post("/models/predict/batch", response_model=Envelope[BatchPredictData])
def models_predict_batch(body: BatchPredictRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.predict_batch(
            customer_ids=body.customer_ids,
            rows=body.rows,
            run_id=body.run_id,
        )
        data = BatchPredictData.model_validate(raw)
        return Envelope[BatchPredictData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/models/curves", response_model=Envelope[CurvesData])
def models_curves(request: Request, run_id: str | None = Query(default=None)):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        data = CurvesData.model_validate(artifacts.get_curves(run_id))
        return Envelope[CurvesData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/models/calibration", response_model=Envelope[dict])
def models_calibration(request: Request, run_id: str | None = Query(default=None)):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        data = artifacts.get_calibration(run_id)
        return Envelope[dict](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/models/lift", response_model=Envelope[LiftData])
def models_lift(request: Request, run_id: str | None = Query(default=None)):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        data = LiftData.model_validate(artifacts.get_lift(run_id))
        return Envelope[LiftData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/models/threshold-scan", response_model=Envelope[ThresholdScanData])
def models_threshold_scan(request: Request, run_id: str | None = Query(default=None)):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        data = ThresholdScanData.model_validate(artifacts.get_threshold_scan(run_id))
        return Envelope[ThresholdScanData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)
