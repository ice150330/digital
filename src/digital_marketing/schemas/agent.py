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
    pi_fallback: bool = Field(default=False, description="默认 runtime=pi 但降级 local/template 时为 True")


class SessionSummaryData(BaseModel):
    session_id: str
    last_user_message: str = ""
    created_at: str
    updated_at: str
    runtime: str
    tool_count: int = 0
    message_count: int = 0


class SessionListData(BaseModel):
    items: list[SessionSummaryData]
    n: int


class SessionDeleteData(BaseModel):
    session_id: str
    deleted: bool
    message: str


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
    # 阶段9：Pi 编排中枢
    is_stub: bool = False
    default_runtime: str | None = None
    skills: list[str] = Field(default_factory=list)
    skills_detail: list[dict[str, Any]] = Field(default_factory=list)
    sessions_count: int = 0
    fallback_reason: str | None = None
    # Stage 5：桥接三要素就绪状态（脚本/node/SDK 包）
    bridge_ready: bool = False
    bridge_note: str | None = None


class ReportRequest(BaseModel):
    title: str = "数字营销转化分析报告"
    sections: list[str] | None = None


class ReportData(BaseModel):
    report_path: str
    title: str
    n_sections: int
    n_sections_ok: int
    digest: str
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: str


class AuditRecentData(BaseModel):
    items: list[dict[str, Any]]
    n: int
    note: str = "按时间倒序；字段见 AGENTS.md §9.4 审计约定"


# ---------------------------------------------------------------------------
# Stage 5：Pi 桥接（工具清单 + loopback 执行）
# ---------------------------------------------------------------------------


class ToolSpecData(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    stage: str = ""


class ToolManifestData(BaseModel):
    tools: list[ToolSpecData]
    n: int


class ToolRunRequest(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolRunData(BaseModel):
    """工具执行结果；ok=False 时 error 为原因（envelope 层仍 ok=True）。"""

    ok: bool
    tool: str
    result: Any = None
    error: str | None = None
