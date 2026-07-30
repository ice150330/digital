"""分群 API。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from digital_marketing.api.errors import from_artifact_error
from digital_marketing.core.paths import resolve_under_root
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.segments import AssignData, AssignRequest, SegmentsData
from digital_marketing.segment.assign import assign_one
from digital_marketing.services import artifacts
from digital_marketing.services.artifacts import ArtifactError

router = APIRouter(tags=["segments"])


@router.get("/segments", response_model=Envelope[SegmentsData])
def list_segments(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        path = resolve_under_root("outputs/segments/summary.json")
        if not path.is_file():
            raise ArtifactError(
                "ARTIFACT_MISSING",
                "缺少分群产物，请运行 python scripts/04_train_cluster.py",
            )
        raw = artifacts.load_json(path)
        data = SegmentsData.model_validate(raw)
        return Envelope[SegmentsData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)


@router.post("/segments/assign", response_model=Envelope[AssignData])
def segments_assign(body: AssignRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = assign_one(customer_id=body.customer_id, features=body.features)
        data = AssignData.model_validate(raw)
        return Envelope[AssignData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)
