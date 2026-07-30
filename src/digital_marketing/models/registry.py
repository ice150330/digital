"""模型 run 注册与加载（文件轨）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from digital_marketing.core.paths import resolve_under_root


def metrics_dir() -> Path:
    return resolve_under_root("outputs/metrics")


def models_dir() -> Path:
    return resolve_under_root("outputs/models")


def list_metric_runs() -> list[dict[str, Any]]:
    d = metrics_dir()
    if not d.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for p in sorted(d.glob("*.json")):
        if p.name == "leaderboard.json":
            continue
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return rows


def load_leaderboard() -> list[dict[str, Any]]:
    path = metrics_dir() / "leaderboard.json"
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_model_bundle(run_id: str) -> tuple[Any, dict[str, Any]]:
    """加载 model.joblib 与 meta.json。"""
    run_dir = models_dir() / run_id
    meta_path = run_dir / "meta.json"
    model_path = run_dir / "model.joblib"
    if not meta_path.is_file() or not model_path.is_file():
        raise FileNotFoundError(f"模型 run 不存在: {run_id}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    model = joblib.load(model_path)
    return model, meta
