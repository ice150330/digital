"""Agent 审计日志（jsonl）与会话落盘。

目录可由 config/agent.yaml 的 audit.log_dir / audit.session_dir 覆盖；
缺省 outputs/agent_logs 与 outputs/agent_sessions。
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from digital_marketing.core.paths import ensure_dir, resolve_under_root

_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _audit_cfg() -> dict[str, Any]:
    """Stage 1：统一经 agent/config.py 缓存加载。"""
    from digital_marketing.agent.config import get_agent_config

    return get_agent_config().audit.model_dump()


def log_dir() -> Path:
    rel = str(_audit_cfg().get("log_dir") or "outputs/agent_logs")
    return ensure_dir(resolve_under_root(rel))


def session_dir() -> Path:
    rel = str(_audit_cfg().get("session_dir") or "outputs/agent_sessions")
    return ensure_dir(resolve_under_root(rel))


def _session_path(session_id: str) -> Path:
    """限制会话文件名，避免路径穿越到会话目录之外。"""
    normalized = str(session_id).strip()
    if not _SESSION_ID_PATTERN.fullmatch(normalized):
        raise ValueError("session_id 格式无效")
    return session_dir() / f"{normalized}.json"


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
    path = _session_path(session_id)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session(session_id: str) -> dict[str, Any] | None:
    path = _session_path(session_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions(limit: int = 30) -> list[dict[str, Any]]:
    """按更新时间倒序返回会话摘要，不读取已软删除目录。"""
    rows: list[dict[str, Any]] = []
    paths = sorted(session_dir().glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for path in paths[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            stat = path.stat()
        except (OSError, json.JSONDecodeError):
            continue
        messages = data.get("messages") if isinstance(data.get("messages"), list) else []
        user_messages = [
            item.get("content")
            for item in messages
            if isinstance(item, dict) and item.get("role") == "user" and isinstance(item.get("content"), str)
        ]
        tool_count = sum(
            len(content.get("tool_trace") or [])
            for item in messages
            if isinstance(item, dict)
            and item.get("role") == "assistant"
            and isinstance((content := item.get("content")), dict)
        )
        rows.append(
            {
                "session_id": str(data.get("session_id") or path.stem),
                "last_user_message": user_messages[-1] if user_messages else "",
                "created_at": datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
                "updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "runtime": str(data.get("runtime") or "unknown"),
                "tool_count": tool_count,
                "message_count": len(messages),
            }
        )
    return rows


def soft_delete_session(session_id: str) -> Path | None:
    """将会话移动到 deleted 子目录，保留本地恢复可能。"""
    source = _session_path(session_id)
    if not source.is_file():
        return None
    deleted_dir = ensure_dir(session_dir() / "deleted")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = deleted_dir / f"{source.stem}-{stamp}.json"
    source.replace(target)
    return target


def now_ms() -> float:
    return time.perf_counter() * 1000
