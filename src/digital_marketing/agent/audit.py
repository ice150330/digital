"""Agent 审计日志（jsonl）与会话落盘。

目录可由 config/agent.yaml 的 audit.log_dir / audit.session_dir 覆盖；
缺省 outputs/agent_logs 与 outputs/agent_sessions。
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from digital_marketing.core.paths import ensure_dir, project_root, resolve_under_root


def _audit_cfg() -> dict[str, Any]:
    path = project_root() / "config" / "agent.yaml"
    if not path.is_file():
        return {}
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return cfg.get("audit") or {}


def log_dir() -> Path:
    rel = str(_audit_cfg().get("log_dir") or "outputs/agent_logs")
    return ensure_dir(resolve_under_root(rel))


def session_dir() -> Path:
    rel = str(_audit_cfg().get("session_dir") or "outputs/agent_sessions")
    return ensure_dir(resolve_under_root(rel))


def append_audit(row: dict[str, Any]) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = log_dir() / f"agent_{day}.jsonl"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **row,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def list_recent(limit: int = 50) -> list[dict[str, Any]]:
    """读最近审计行（跨多日文件，按文件名倒序取尾部）。"""
    d = log_dir()
    if not d.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(d.glob("agent_*.jsonl"), reverse=True):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(rows) >= limit:
                return rows
    return rows


def save_session(session_id: str, data: dict[str, Any]) -> Path:
    path = session_dir() / f"{session_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session(session_id: str) -> dict[str, Any] | None:
    path = session_dir() / f"{session_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def now_ms() -> float:
    return time.perf_counter() * 1000
