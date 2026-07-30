"""Agent 服务门面。"""

from __future__ import annotations

from typing import Any

from digital_marketing.agent import audit
from digital_marketing.agent.local_runtime import resolve_runtime, run_local_chat


def chat(
    message: str,
    *,
    session_id: str | None = None,
    runtime: str | None = None,
    request_id: str = "unknown",
) -> dict[str, Any]:
    if not message or not str(message).strip():
        raise ValueError("message 不能为空")
    return run_local_chat(
        str(message).strip(),
        session_id=session_id,
        runtime=runtime,
        request_id=request_id,
    )


def get_session(session_id: str) -> dict[str, Any] | None:
    return audit.load_session(session_id)


def current_runtime() -> str:
    return resolve_runtime(None)
