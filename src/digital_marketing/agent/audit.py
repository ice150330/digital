"""Agent 审计日志（jsonl）。"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from digital_marketing.core.paths import ensure_dir, resolve_under_root


def _log_dir() -> Path:
    return ensure_dir(resolve_under_root("outputs/agent_logs"))


def _session_dir() -> Path:
    return ensure_dir(resolve_under_root("outputs/agent_sessions"))


def append_audit(row: dict[str, Any]) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = _log_dir() / f"agent_{day}.jsonl"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **row,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def save_session(session_id: str, data: dict[str, Any]) -> Path:
    path = _session_dir() / f"{session_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session(session_id: str) -> dict[str, Any] | None:
    path = _session_dir() / f"{session_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def now_ms() -> float:
    return time.perf_counter() * 1000
