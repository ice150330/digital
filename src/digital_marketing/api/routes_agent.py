"""Agent 路由。"""

from __future__ import annotations

import json
import queue
import threading
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from digital_marketing.agent import audit as agent_audit
from digital_marketing.agent import service as agent_service
from digital_marketing.agent.config import get_pi_agent_settings, update_pi_agent_settings
from digital_marketing.agent.llm_client import LlmUnavailableError
from digital_marketing.agent.model_catalog import UpstreamModelError, fetch_upstream_models
from digital_marketing.agent.pi_runtime import pi_status
from digital_marketing.agent.report import generate_analysis_report
from digital_marketing.api.errors import envelope_error
from digital_marketing.agent.tools import list_tool_manifest, run_tool
from digital_marketing.schemas.agent import (
    AuditRecentData,
    ChatData,
    ChatRequest,
    PiAgentConfigData,
    PiAgentConfigUpdate,
    PiModelListData,
    PiStatusData,
    ReportData,
    ReportRequest,
    RuntimeData,
    RuntimeRequest,
    SessionDeleteData,
    SessionListData,
    ToolManifestData,
    ToolRunData,
    ToolRunRequest,
)
from digital_marketing.schemas.common import Envelope

router = APIRouter(tags=["agent"])


def _loopback_base(request: Request) -> str:
    """Pi 桥接 loopback 基址：用真实请求端口回指宿主，避免硬编码 9800。"""
    from digital_marketing.core.config import get_settings

    port = request.url.port or 9800
    return f"http://127.0.0.1:{port}{get_settings().api_prefix}"


@router.post("/agent/chat", response_model=Envelope[ChatData])
def agent_chat(body: ChatRequest, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = agent_service.chat(
            body.message,
            session_id=body.session_id,
            runtime=body.runtime,
            request_id=request_id,
            api_base=_loopback_base(request),
        )
        data = ChatData.model_validate(raw)
        return Envelope[ChatData](ok=True, data=data, error=None, request_id=request_id)
    except ValueError as e:
        return envelope_error(request, code="VALIDATION_ERROR", message=str(e), status_code=422)
    except LlmUnavailableError as e:
        return envelope_error(
            request,
            code=e.code,
            message=e.message,
            detail=e.detail,
            status_code=502,
        )
    except Exception as e:  # noqa: BLE001
        return envelope_error(
            request,
            code="AGENT_TOOL_FAILED",
            message=f"Agent 执行失败: {e}",
            status_code=500,
        )


@router.post("/agent/chat/stream")
def agent_chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    """SSE 对话：工具开始/结束、图表、契约段与文本增量从同一连接推送。"""
    request_id = getattr(request.state, "request_id", "unknown")
    events: queue.Queue[tuple[str, dict[str, Any]] | None] = queue.Queue()
    emitted_done = False

    def emit(event: str, data: dict[str, Any]) -> None:
        nonlocal emitted_done
        if event == "done":
            emitted_done = True
        events.put((event, data))

    def worker() -> None:
        try:
            result = agent_service.chat(
                body.message,
                session_id=body.session_id,
                runtime=body.runtime,
                request_id=request_id,
                on_event=emit,
                api_base=_loopback_base(request),
            )
            if not emitted_done:
                emit(
                    "done",
                    {
                        "session_id": result.get("session_id"),
                        "latency_ms": result.get("latency_ms"),
                        "runtime": result.get("runtime"),
                        "pi_fallback": bool(result.get("pi_fallback")),
                        "pi_status": result.get("pi_status"),
                    },
                )
        except ValueError as exc:
            emit("error", {"code": "VALIDATION_ERROR", "message": str(exc)})
        except LlmUnavailableError as exc:
            emit("error", {"code": exc.code, "message": exc.message, "detail": exc.detail})
        except Exception as exc:  # noqa: BLE001
            emit("error", {"code": "AGENT_TOOL_FAILED", "message": f"Agent 执行失败: {exc}"})
        finally:
            events.put(None)

    threading.Thread(target=worker, name=f"agent-sse-{request_id[:8]}", daemon=True).start()

    def event_stream():
        while True:
            item = events.get()
            if item is None:
                break
            event, data = item
            payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            yield f"event: {event}\ndata: {payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agent/sessions", response_model=Envelope[SessionListData])
def agent_sessions(request: Request, limit: int = Query(default=30, ge=1, le=100)):
    """返回最近会话摘要，供 Agent 页直接加载。"""
    request_id = getattr(request.state, "request_id", "unknown")
    items = agent_audit.list_sessions(limit=limit)
    data = SessionListData(items=items, n=len(items))
    return Envelope[SessionListData](ok=True, data=data, error=None, request_id=request_id)


@router.get("/agent/sessions/{session_id}", response_model=Envelope[dict])
def agent_session(session_id: str, request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        data = agent_service.get_session(session_id)
    except ValueError as exc:
        return envelope_error(request, code="VALIDATION_ERROR", message=str(exc), status_code=422)
    if not data:
        return envelope_error(
            request,
            code="ARTIFACT_MISSING",
            message=f"会话不存在: {session_id}",
            status_code=404,
        )
    return Envelope[dict](ok=True, data=data, error=None, request_id=request_id)


@router.delete("/agent/sessions/{session_id}", response_model=Envelope[SessionDeleteData])
def agent_session_delete(session_id: str, request: Request):
    """软删除会话：移动到 outputs/agent_sessions/deleted/，不直接销毁。"""
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        target = agent_audit.soft_delete_session(session_id)
    except ValueError as exc:
        return envelope_error(request, code="VALIDATION_ERROR", message=str(exc), status_code=422)
    if target is None:
        return envelope_error(
            request,
            code="ARTIFACT_MISSING",
            message=f"会话不存在: {session_id}",
            status_code=404,
        )
    data = SessionDeleteData(session_id=session_id, deleted=True, message="会话已移入可恢复的 deleted 目录")
    return Envelope[SessionDeleteData](ok=True, data=data, error=None, request_id=request_id)


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


@router.get("/agent/pi/config", response_model=Envelope[PiAgentConfigData])
def agent_pi_config(request: Request):
    """PiAgent 配置卡片：返回可保存 settings + 当前 status（不回显密钥明文）。"""
    request_id = getattr(request.state, "request_id", "unknown")
    data = PiAgentConfigData.model_validate(
        {
            "settings": get_pi_agent_settings(),
            "status": pi_status(),
        }
    )
    return Envelope[PiAgentConfigData](ok=True, data=data, error=None, request_id=request_id)


@router.put("/agent/pi/config", response_model=Envelope[PiAgentConfigData])
def agent_pi_config_update(body: PiAgentConfigUpdate, request: Request):
    """保存 PiAgent 非密钥配置；API Key 仅写入本地 .env 的 DEEPSEEK_API_KEY。"""
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        settings = update_pi_agent_settings(body.model_dump(exclude_unset=True))
        data = PiAgentConfigData.model_validate({"settings": settings, "status": pi_status()})
        return Envelope[PiAgentConfigData](ok=True, data=data, error=None, request_id=request_id)
    except ValueError as exc:
        return envelope_error(request, code="VALIDATION_ERROR", message=str(exc), status_code=422)


@router.get("/agent/pi/models", response_model=Envelope[PiModelListData])
def agent_pi_models(request: Request):
    """从已保存的上游 Base URL 读取可选模型列表；API Key 不返回给前端。"""
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        raw = fetch_upstream_models()
        data = PiModelListData.model_validate(raw)
        return Envelope[PiModelListData](ok=True, data=data, error=None, request_id=request_id)
    except UpstreamModelError as exc:
        status = 422 if exc.code == "VALIDATION_ERROR" else 502
        return envelope_error(
            request,
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
            status_code=status,
        )


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
