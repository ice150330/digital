"""全局 / 局部解释 + PDP / 反事实（模型行为口径）。"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from digital_marketing.api.errors import from_artifact_error
from digital_marketing.schemas.advanced import (
    CounterfactualData,
    CounterfactualRequest,
    PdpData,
)
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.explain import (
    CustomerExplainData,
    CustomerExplainRequest,
    GlobalExplainData,
)
from digital_marketing.services import artifacts
from digital_marketing.services.artifacts import ArtifactError

router = APIRouter(tags=["explain"])


@router.get("/explain/global", response_model=Envelope[GlobalExplainData])
def explain_global(request: Request, run_id: str | None = Query(default=None)):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.get_global_explain(run_id)
        data = GlobalExplainData.model_validate(raw)
        return Envelope[GlobalExplainData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.post("/explain/customer", response_model=Envelope[CustomerExplainData])
def explain_customer(body: CustomerExplainRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.explain_customer(
            customer_id=body.customer_id,
            features=body.features,
            run_id=body.run_id,
            top_k=body.top_k,
        )
        data = CustomerExplainData.model_validate(raw)
        return Envelope[CustomerExplainData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.get("/explain/pdp", response_model=Envelope[PdpData])
def explain_pdp(
    request: Request,
    feature: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        data = PdpData.model_validate(artifacts.get_pdp(run_id, feature))
        return Envelope[PdpData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.post("/explain/counterfactual", response_model=Envelope[CounterfactualData])
def explain_counterfactual(body: CounterfactualRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.counterfactual_customer(
            customer_id=body.customer_id,
            features=body.features,
            feature=body.feature,
            target_proba=body.target_proba,
            run_id=body.run_id,
            grid_size=body.grid_size,
            max_steps=body.max_steps,
        )
        data = CounterfactualData.model_validate(raw)
        return Envelope[CounterfactualData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)
    except ValueError as e:
        from digital_marketing.api.errors import envelope_error

        return envelope_error(request, code="VALIDATION_ERROR", message=str(e), status_code=422)
