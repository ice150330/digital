"""API 错误辅助。"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from digital_marketing.schemas.common import ApiError, Envelope
from digital_marketing.services.artifacts import ArtifactError


def envelope_error(
    request: Request,
    *,
    code: str,
    message: str,
    detail: dict | None = None,
    status_code: int = 400,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    body = Envelope(
        ok=False,
        data=None,
        error=ApiError(code=code, message=message, detail=detail or {}),
        request_id=request_id,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def from_artifact_error(request: Request, exc: ArtifactError) -> JSONResponse:
    status = 404
    if exc.code in {"VALIDATION_ERROR"}:
        status = 422
    elif exc.code in {"MODEL_NOT_LOADED", "ARTIFACT_MISSING"}:
        status = 404
    return envelope_error(
        request,
        code=exc.code,
        message=exc.message,
        detail=exc.detail,
        status_code=status,
    )
