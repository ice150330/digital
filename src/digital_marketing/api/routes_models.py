"""模型指标与预测。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from digital_marketing.api.errors import from_artifact_error
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.models import MetricsListData, PredictData, PredictRequest
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
