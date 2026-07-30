"""Agent DTO。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    runtime: str | None = None  # local | template | pi


class ChatData(BaseModel):
    runtime: str
    session_id: str
    reply: str
    observed_facts: list[str] = Field(default_factory=list)
    inferences: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
    latency_ms: float | None = None
    pi_status: dict[str, Any] | None = None


class RuntimeRequest(BaseModel):
    runtime: str


class RuntimeData(BaseModel):
    runtime: str
    message: str | None = None


class PiStatusData(BaseModel):
    installed: bool
    executable: str | None = None
    valid_prefix: bool = True
    code: str | None = None
    message: str | None = None
    hint: str | None = None
