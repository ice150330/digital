"""关联规则 API。"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from digital_marketing.api.errors import from_artifact_error
from digital_marketing.core.paths import resolve_under_root
from digital_marketing.schemas.common import Envelope
from digital_marketing.schemas.rules import RulesData
from digital_marketing.services import artifacts
from digital_marketing.services.artifacts import ArtifactError

router = APIRouter(tags=["rules"])


@router.get("/rules", response_model=Envelope[RulesData])
def list_rules(
    request: Request,
    min_lift: float = Query(default=1.0),
    limit: int = Query(default=50, ge=1, le=200),
):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        path = resolve_under_root("outputs/rules/top_rules.json")
        if not path.is_file():
            raise ArtifactError(
                "ARTIFACT_MISSING",
                "缺少关联规则产物，请运行 python scripts/05_mine_rules.py",
            )
        raw = artifacts.load_json(path)
        rules = [r for r in (raw.get("rules") or []) if float(r.get("lift") or 0) >= min_lift]
        rules = rules[:limit]
        data = RulesData(
            method=raw.get("method"),
            n_rules=len(rules),
            min_lift=min_lift,
            disclaimer=raw.get("disclaimer") or RulesData.model_fields["disclaimer"].default,
            rules=rules,
        )
        return Envelope[RulesData](ok=True, data=data, error=None, request_id=request_id)
    except ArtifactError as e:
        return from_artifact_error(request, e)
