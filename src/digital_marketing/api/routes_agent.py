"""Agent 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from digital_marketing.agent import audit as agent_audit
from digital_marketing.agent import service as agent_service
from digital_marketing.agent.pi_runtime import pi_status
from digital_marketing.agent.report import generate_analysis_report
from digital_marketing.api.errors import envelope_error
from digital_marketing.agent.tools import list_tool_manifest, run_tool
from digital_marketing.schemas.agent import (
    AuditRecentData,
    ChatData,
    ChatRequest,
    PiStatusData,
    ReportData,
    ReportRequest,
    RuntimeData,
    RuntimeRequest,
    ToolManifestData,
    ToolRunData,
    ToolRunRequest,
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
    # Stage 1：写回 + 缓存失效统一经 agent.config.set_runtime_persisted
    from digital_marketing.agent.config import set_runtime_persisted

    set_runtime_persisted(rt)
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


@router.get("/agent/tools/manifest", response_model=Envelope[ToolManifestData])
def agent_tools_manifest(request: Request):
    """Stage 5：Pi 桥接工具清单（宿主 @tool 声明为唯一真相）。"""
    request_id = getattr(request.state, "request_id", "unknown")
    items = list_tool_manifest()
    data = ToolManifestData(tools=items, n=len(items))
    return Envelope[ToolManifestData](ok=True, data=data, error=None, request_id=request_id)


@router.post("/agent/tool-run", response_model=Envelope[ToolRunData])
def agent_tool_run(body: ToolRunRequest, request: Request):
    """Stage 5：Pi 桥接 loopback 执行口——工具仍由宿主 REGISTRY 实际执行（§9.1）。

    Pi 经 customTools 代理调用本端点；数字永远出自宿主，Pi 只编排与叙述。
    """
    request_id = getattr(request.state, "request_id", "unknown")
    out = run_tool(body.name, **(body.args or {}))
    data = ToolRunData(
        ok=bool(out.get("ok")),
        tool=str(out.get("tool") or body.name),
        result=out.get("result"),
        error=out.get("error"),
    )
    return Envelope[ToolRunData](ok=True, data=data, error=None, request_id=request_id)


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
