"""模拟器路由：预算分配（期望值口径）。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from digital_marketing.api.errors import envelope_error, from_artifact_error
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.simulate import BudgetSimulateData, BudgetSimulateRequest
from digital_marketing.services import artifacts
from digital_marketing.services.artifacts import ArtifactError

router = APIRouter(tags=["simulate"])


@router.post("/simulate/budget", response_model=Envelope[BudgetSimulateData])
def simulate_budget(body: BudgetSimulateRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = artifacts.simulate_budget(
            budget=body.budget,
            value_per_conversion=body.value_per_conversion,
            cost_per_contact=body.cost_per_contact,
            run_id=body.run_id,
            export=body.export,
            n_points=body.n_points,
        )
        data = BudgetSimulateData.model_validate(raw)
        return Envelope[BudgetSimulateData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)
    except ValueError as e:
        return envelope_error(request, code="VALIDATION_ERROR", message=str(e), status_code=422)
