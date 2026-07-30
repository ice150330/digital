"""统一 API envelope 与公共 DTO。"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class Envelope(BaseModel, Generic[T]):
    ok: bool
    data: T | None = None
    error: ApiError | None = None
    request_id: str


class HealthData(BaseModel):
    status: str  # ok | degraded
    app: str
    version: str
    database_ok: bool
    campaigns_count: int | None = None
    message: str | None = None
