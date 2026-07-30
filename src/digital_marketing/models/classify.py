"""分类实验：E0 Dummy / E1 Logistic / E3 LightGBM（失败回退 RF）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import yaml
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from digital_marketing.core.paths import ensure_dir, project_root
from digital_marketing.models.metrics import evaluate_at_threshold, search_threshold_f1

logger = logging.getLogger(__name__)


def load_model_config(path: Path | None = None) -> dict[str, Any]:
    path = path or (project_root() / "config" / "model.yaml")
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_estimator(kind: str, *, class_weight: str | None, seed: int, fallback: str | None):
    kind = kind.lower()
    if kind == "dummy":
        return DummyClassifier(strategy="prior", random_state=seed)
    if kind == "logistic":
        return LogisticRegression(
            max_iter=2000,
            class_weight=class_weight,
            random_state=seed,
            solver="lbfgs",
        )
    if kind in {"lightgbm", "lgbm"}:
        try:
            import lightgbm as lgb

            return lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                num_leaves=31,
                class_weight=class_weight,
                random_state=seed,
                verbosity=-1,
            )
        except Exception as e:  # noqa: BLE001 — 明确回退
            logger.warning("LightGBM 不可用 (%s)，回退 %s", e, fallback or "random_forest")
            kind = (fallback or "random_forest").lower()
    if kind in {"random_forest", "rf"}:
        return RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            class_weight=class_weight,
            random_state=seed,
            n_jobs=-1,
        )
    raise ValueError(f"未知模型 kind: {kind}")


def _predict_proba_positive(model, X: np.ndarray) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        # 二分类取正类列；若仅一类则全 1 或 0
        if proba.shape[1] == 1:
            # Dummy 等可能只有一类
            classes = list(getattr(model, "classes_", [1]))
            if classes[0] == 1:
                return proba[:, 0]
            return 1.0 - proba[:, 0]
        # 找到 label=1 的列
        classes = list(model.classes_)
        if 1 in classes:
            return proba[:, classes.index(1)]
        return proba[:, -1]
    # 无 proba 则用 decision 或 predict
    pred = model.predict(X)
    return pred.astype(float)


def run_experiment(
    *,
    exp: dict[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_valid: np.ndarray,
    y_valid: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    seed: int,
    models_dir: Path,
    metrics_dir: Path,
    feature_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """训练单实验，valid 搜阈值，test 评估，落盘 model+metrics。"""
    exp_id = str(exp["id"])
    name = str(exp.get("name", exp_id))
    kind = str(exp.get("kind", "dummy"))
    class_weight = exp.get("class_weight")
    fallback = exp.get("fallback")

    model = _build_estimator(kind, class_weight=class_weight, seed=seed, fallback=fallback)
    model.fit(X_train, y_train)

    proba_valid = _predict_proba_positive(model, X_valid)
    thr_cfg = load_model_config().get("threshold") or {}
    threshold, valid_f1 = search_threshold_f1(
        y_valid,
        proba_valid,
        start=float(thr_cfg.get("grid_start", 0.05)),
        stop=float(thr_cfg.get("grid_stop", 0.95)),
        step=float(thr_cfg.get("grid_step", 0.01)),
    )

    proba_test = _predict_proba_positive(model, X_test)
    test_metrics = evaluate_at_threshold(y_test, proba_test, threshold)
    proba_train = _predict_proba_positive(model, X_train)
    train_pr = float(__import__("sklearn.metrics", fromlist=["average_precision_score"]).average_precision_score(y_train, proba_train))

    run_id = f"{exp_id}_{name}"
    run_dir = ensure_dir(Path(models_dir) / run_id)
    model_path = run_dir / "model.joblib"
    meta_path = run_dir / "meta.json"
    joblib.dump(model, model_path)

    created = datetime.now(timezone.utc).isoformat()
    meta = {
        "run_id": run_id,
        "exp_id": exp_id,
        "model_name": name,
        "kind": kind,
        "threshold": threshold,
        "valid_f1_at_threshold": valid_f1,
        "seed": seed,
        "created_at": created,
        "model_path": str(model_path),
        "feature_schema": feature_schema or {},
        "notes": {
            "accuracy_is_reference_only": True,
            "primary_metric": "pr_auc",
        },
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    metrics_payload = {
        "run_id": run_id,
        "exp_id": exp_id,
        "model_name": name,
        "split": "test",
        "threshold": threshold,
        "train_pr_auc": train_pr,
        "valid_f1_at_threshold": valid_f1,
        **test_metrics,
        "accuracy_note": "仅对照；请以 PR-AUC / F1 为主，并并列 Dummy",
    }
    metrics_dir = ensure_dir(Path(metrics_dir))
    metrics_path = metrics_dir / f"{run_id}.json"
    metrics_path.write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metrics_payload["metrics_path"] = str(metrics_path)
    metrics_payload["meta_path"] = str(meta_path)
    return metrics_payload


def write_leaderboard(rows: list[dict[str, Any]], metrics_dir: Path) -> Path:
    """按 pr_auc 降序写 leaderboard.json。"""
    metrics_dir = ensure_dir(Path(metrics_dir))
    ranked = sorted(rows, key=lambda r: (r.get("pr_auc") is not None, r.get("pr_auc") or 0), reverse=True)
    slim = [
        {
            "run_id": r.get("run_id"),
            "exp_id": r.get("exp_id"),
            "model_name": r.get("model_name"),
            "pr_auc": r.get("pr_auc"),
            "roc_auc": r.get("roc_auc"),
            "f1": r.get("f1"),
            "accuracy": r.get("accuracy"),
            "threshold": r.get("threshold"),
        }
        for r in ranked
    ]
    path = metrics_dir / "leaderboard.json"
    path.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
