"""Agent 服务门面（Stage 1：runtime 分发上提至此层）。

- runtime=pi → pi_runtime.run_pi_chat（内部含降级链，降级仍走 local/template）
- 其余 → local_runtime.run_local_chat
会话 ID 统一在本层生成，保证两条路径与审计/会话落盘口径一致。
"""

from __future__ import annotations

import uuid
from typing import Any

from digital_marketing.agent import audit
from digital_marketing.agent import pi_runtime
from digital_marketing.agent.local_runtime import EventSink, resolve_runtime, run_local_chat


def chat(
    message: str,
    *,
    session_id: str | None = None,
    runtime: str | None = None,
    request_id: str = "unknown",
    on_event: EventSink | None = None,
) -> dict[str, Any]:
    if not message or not str(message).strip():
        raise ValueError("message 不能为空")
    msg = str(message).strip()
    sid = session_id or str(uuid.uuid4())
    rt = resolve_runtime(runtime)
    if rt == "pi":
        return pi_runtime.run_pi_chat(msg, session_id=sid, request_id=request_id, on_event=on_event)
    return run_local_chat(msg, session_id=sid, runtime=rt, request_id=request_id, on_event=on_event)


def get_session(session_id: str) -> dict[str, Any] | None:
    return audit.load_session(session_id)


def current_runtime() -> str:
    return resolve_runtime(None)
