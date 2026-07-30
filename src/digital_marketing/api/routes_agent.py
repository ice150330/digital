"""Agent 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from digital_marketing.agent import audit as agent_audit
from digital_marketing.agent import service as agent_service
from digital_marketing.agent.pi_runtime import pi_status
from digital_marketing.agent.report import generate_analysis_report
from digital_marketing.api.errors import envelope_error
from digital_marketing.core.paths import project_root
from digital_marketing.schemas.agent import (
    AuditRecentData,
    ChatData,
    ChatRequest,
    PiStatusData,
    ReportData,
    ReportRequest,
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


@router.get("/agent/audit/recent", response_model=Envelope[AuditRecentData])
def agent_audit_recent(request: Request, limit: int = Query(default=50, ge=1, le=500)):
    """最近审计行（outputs/agent_logs/*.jsonl 尾部，时间倒序）。"""
    request_id = getattr(request.state, "request_id", "unknown")
    items = agent_audit.list_recent(limit=limit)
    data = AuditRecentData(items=items, n=len(items))
    return Envelope[AuditRecentData](ok=True, data=data, error=None, request_id=request_id)


@router.post("/agent/report", response_model=Envelope[ReportData])
def agent_report(body: ReportRequest, request: Request):
    """一键生成分析报告（编排只读工具 → markdown 落盘 outputs/reports/）。"""
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = generate_analysis_report(title=body.title, sections=body.sections)
        # 报告生成也入审计
        agent_audit.append_audit(
            {
                "request_id": request_id,
                "session_id": None,
                "runtime": "report",
                "user_message": f"generate_report title={body.title}",
                "tool_calls": [
                    {"tool": t.get("tool"), "ok": t.get("ok")} for t in raw.get("tool_trace", [])
                ],
                "reply_digest": raw.get("digest", "")[:500],
                "latency_ms": None,
                "error": None,
            }
        )
        data = ReportData.model_validate(raw)
        return Envelope[ReportData](ok=True, data=data, error=None, request_id=request_id)
    except Exception as e:  # noqa: BLE001
        return envelope_error(
            request,
            code="AGENT_TOOL_FAILED",
            message=f"报告生成失败: {e}",
            status_code=500,
        )
