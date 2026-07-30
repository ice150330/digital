"""Agent 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from digital_marketing.agent import service as agent_service
from digital_marketing.agent.pi_runtime import pi_status
from digital_marketing.api.errors import envelope_error
from digital_marketing.core.paths import project_root
from digital_marketing.schemas.agent import (
    ChatData,
    ChatRequest,
    PiStatusData,
    RuntimeData,
    RuntimeRequest,
)
from digital_marketing.schemas.common import Envelope

router = APIRouter(tags=["agent"])


@router.post("/agent/chat", response_model=Envelope[ChatData])
def agent_chat(body: ChatRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = agent_service.chat(
            body.message,
            session_id=body.session_id,
            runtime=body.runtime,
            request_id=request_id,
        )
        data = ChatData.model_validate(raw)
        return Envelope[ChatData](ok=True, data=data, error=None, request_id=request_id)
    except ValueError as e:
        return envelope_error(request, code="VALIDATION_ERROR", message=str(e), status_code=422)
    except Exception as e:  # noqa: BLE001
        return envelope_error(
            request,
            code="AGENT_TOOL_FAILED",
            message=f"Agent 执行失败: {e}",
            status_code=500,
        )


@router.get("/agent/sessions/{session_id}", response_model=Envelope[dict])
def agent_session(session_id: str, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    data = agent_service.get_session(session_id)
    if not data:
        return envelope_error(
            request,
            code="ARTIFACT_MISSING",
            message=f"会话不存在: {session_id}",
            status_code=404,
        )
    return Envelope[dict](ok=True, data=data, error=None, request_id=request_id)


@router.post("/agent/runtime", response_model=Envelope[RuntimeData])
def agent_runtime(body: RuntimeRequest, request: Request):
    """写入 config/agent.yaml 的 runtime 字段（本地开发用）。"""
    request_id = getattr(request.state, "request_id", "unknown")
    rt = body.runtime.lower().strip()
    if rt not in {"local", "template", "pi"}:
        return envelope_error(
            request,
            code="VALIDATION_ERROR",
            message="runtime 仅支持 local | template | pi",
            status_code=422,
        )
    import yaml

    path = project_root() / "config" / "agent.yaml"
    cfg = {}
    if path.is_file():
        cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cfg["runtime"] = rt
    path.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    data = RuntimeData(runtime=rt, message=f"已切换 runtime={rt}")
    return Envelope[RuntimeData](ok=True, data=data, error=None, request_id=request_id)


@router.get("/agent/pi/status", response_model=Envelope[PiStatusData])
def agent_pi_status(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    raw = pi_status()
    data = PiStatusData.model_validate(raw)
    return Envelope[PiStatusData](ok=True, data=data, error=None, request_id=request_id)
