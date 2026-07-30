"""分类实验：E0 Dummy / E1 Logistic / E2 默认树 / E3 LightGBM（失败回退 RF）
/ E4 SMOTE / E5-E6 消融 / E7 Stacking / E8 校准。

阶段9：run_experiment 统一产出增强评估（CV、bootstrap CI、PR/ROC 曲线、
lift 十分位、成本敏感阈值扫描）；E5/E6 消融 run 打上标记，
默认 run 选择必须排除含 ConversionRate 的泄漏消融 run。
"""

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
from digital_marketing.models.metrics import (
    bootstrap_pr_auc_ci,
    cv_pr_auc_summary,
    evaluate_at_threshold,
    lift_deciles,
    pr_curve_points,
    roc_curve_points,
    search_threshold_f1,
    threshold_scan,
)

logger = logging.getLogger(__name__)


class SmoteUnavailableError(RuntimeError):
    """imbalanced-learn 未安装，SMOTE 实验不可用（调用方应跳过并声明）。"""


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
    if kind == "stacking":
        from digital_marketing.models.ensemble import build_stacking

        return build_stacking(seed=seed, class_weight=class_weight)
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


def _smote_resample(X: np.ndarray, y: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """仅对 train 做 SMOTE；imbalanced-learn 缺失时抛 SmoteUnavailableError。"""
    try:
        from imblearn.over_sampling import SMOTE
    except Exception as e:  # noqa: BLE001
        raise SmoteUnavailableError(f"imbalanced-learn 不可用: {e}") from e
    X_res, y_res = SMOTE(random_state=seed).fit_resample(X, y)
    return np.asarray(X_res), np.asarray(y_res)


def _cv_factory_for(exp: dict[str, Any], *, seed: int):
    """返回无参 factory：构造与实验同配置的未 fit 估计器（SMOTE 时包 fold 内管线）。"""
    kind = str(exp.get("kind", "dummy"))
    class_weight = exp.get("class_weight")
    fallback = exp.get("fallback")
    use_smote = bool(exp.get("smote"))

    if use_smote:
        try:
            from imblearn.over_sampling import SMOTE
            from imblearn.pipeline import Pipeline as ImbPipeline
        except Exception as e:  # noqa: BLE001
            raise SmoteUnavailableError(f"imbalanced-learn 不可用: {e}") from e

        def factory_smote():
            est = _build_estimator(kind, class_weight=class_weight, seed=seed, fallback=fallback)
            return ImbPipeline([("smote", SMOTE(random_state=seed)), ("clf", est)])

        return factory_smote

    def factory():
        return _build_estimator(kind, class_weight=class_weight, seed=seed, fallback=fallback)

    return factory


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
    transformer: Any | None = None,
    enhanced: bool = True,
    cost_fn: float = 5.0,
    cost_fp: float = 1.0,
) -> dict[str, Any]:
    """训练单实验，valid 搜阈值（+可选校准），test 评估，落盘 model+metrics。

    - exp.smote: true → 仅 train SMOTE（imblearn 缺失抛 SmoteUnavailableError）
    - exp.calibrate: true → valid 上 Platt/Isotonic 择优校准，校准后概率搜阈值
    - enhanced: 追加 CV / bootstrap CI / PR / ROC / lift / 阈值扫描
    - transformer: 传入则随 run 目录落盘（E5/E6 等特征变体的 per-run transformer）
    """
    exp_id = str(exp["id"])
    name = str(exp.get("name", exp_id))
    kind = str(exp.get("kind", "dummy"))
    class_weight = exp.get("class_weight")
    fallback = exp.get("fallback")
    ablation = exp.get("ablation")
    includes_cr = bool(exp.get("includes_conversion_rate"))

    # --- fit（可选 SMOTE，仅 train） ---
    X_fit, y_fit = X_train, y_train
    smote_note = None
    if exp.get("smote"):
        X_fit, y_fit = _smote_resample(X_train, y_train, seed)
        smote_note = f"SMOTE 仅 train: {len(y_train)}→{len(y_fit)}"

    model = _build_estimator(kind, class_weight=class_weight, seed=seed, fallback=fallback)
    model.fit(X_fit, y_fit)

    # --- 可选校准（valid fit，test 不参与） ---
    calib_payload: dict[str, Any] | None = None
    proba_valid_raw = _predict_proba_positive(model, X_valid)
    if exp.get("calibrate"):
        from digital_marketing.models.calibrate import calibration_report, fit_best_calibrator

        proba_test_raw = _predict_proba_positive(model, X_test)
        model, calib_method, valid_cmp = fit_best_calibrator(model, X_valid, y_valid)
        proba_valid = _predict_proba_positive(model, X_valid)
        proba_test = _predict_proba_positive(model, X_test)
        calib_payload = calibration_report(
            y_test, proba_test_raw, proba_test, method=calib_method, valid_brier_compare=valid_cmp
        )
    else:
        proba_valid = proba_valid_raw
        proba_test = _predict_proba_positive(model, X_test)

    # --- valid 搜阈值（校准后概率），test 一次评估 ---
    thr_cfg = load_model_config().get("threshold") or {}
    threshold, valid_f1 = search_threshold_f1(
        y_valid,
        proba_valid,
        start=float(thr_cfg.get("grid_start", 0.05)),
        stop=float(thr_cfg.get("grid_stop", 0.95)),
        step=float(thr_cfg.get("grid_step", 0.01)),
    )

    test_metrics = evaluate_at_threshold(y_test, proba_test, threshold)
    proba_train = _predict_proba_positive(model, X_train)
    train_pr = float(
        __import__("sklearn.metrics", fromlist=["average_precision_score"]).average_precision_score(
            y_train, proba_train
        )
    )

    # --- 增强评估统计（均不重训） ---
    extra: dict[str, Any] = {}
    if enhanced:
        try:
            factory = _cv_factory_for(exp, seed=seed)
            extra["cv"] = cv_pr_auc_summary(factory, X_train, y_train, folds=5, seed=seed)
        except SmoteUnavailableError:
            raise
        except Exception as e:  # noqa: BLE001 — CV 失败不阻塞主流程
            logger.warning("CV 评估失败 %s: %s", exp_id, e)
            extra["cv"] = {"error": str(e)}
        extra["ci"] = bootstrap_pr_auc_ci(y_test, proba_test, n_boot=1000, seed=seed)
        extra["pr_curve"] = pr_curve_points(y_test, proba_test)
        extra["roc_curve"] = roc_curve_points(y_test, proba_test)
        extra["lift_deciles"] = lift_deciles(y_test, proba_test)
        extra["threshold_scan"] = threshold_scan(
            y_test, proba_test, cost_fp=cost_fp, cost_fn=cost_fn
        )

    run_id = f"{exp_id}_{name}"
    run_dir = ensure_dir(Path(models_dir) / run_id)
    model_path = run_dir / "model.joblib"
    meta_path = run_dir / "meta.json"
    joblib.dump(model, model_path)
    if transformer is not None:
        joblib.dump(transformer, run_dir / "transformer.joblib")

    created = datetime.now(timezone.utc).isoformat()
    meta = {
        "run_id": run_id,
        "exp_id": exp_id,
        "model_name": name,
        "kind": kind,
        "calibrated": bool(exp.get("calibrate")),
        "calibration_method": (calib_payload or {}).get("method"),
        "smote": bool(exp.get("smote")),
        "ablation": ablation,
        "includes_conversion_rate": includes_cr,
        "threshold": threshold,
        "valid_f1_at_threshold": valid_f1,
        "seed": seed,
        "created_at": created,
        "model_path": str(model_path),
        "has_run_transformer": transformer is not None,
        "feature_schema": feature_schema or {},
        "notes": {
            "accuracy_is_reference_only": True,
            "primary_metric": "pr_auc",
            "smote_note": smote_note,
            "ablation_note": (
                "泄漏/消融实验：不参选默认 run" if (ablation or includes_cr) else None
            ),
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
        "ablation": ablation,
        "includes_conversion_rate": includes_cr,
        **test_metrics,
        **extra,
        "accuracy_note": "仅对照；请以 PR-AUC / F1 为主，并并列 Dummy",
    }
    if calib_payload is not None:
        metrics_payload["brier"] = calib_payload["after"]["brier"]
        metrics_payload["calibration_method"] = calib_payload["method"]
        # 校准对比单独落盘，供 GET /models/calibration
        calib_path = ensure_dir(Path(metrics_dir)) / f"calibration_{run_id}.json"
        calib_path.write_text(
            json.dumps({"run_id": run_id, **calib_payload}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

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
    """按 pr_auc 降序写 leaderboard.json（含 CV/CI/校准/消融标记）。"""
    metrics_dir = ensure_dir(Path(metrics_dir))
    ranked = sorted(rows, key=lambda r: (r.get("pr_auc") is not None, r.get("pr_auc") or 0), reverse=True)
    slim = []
    for r in ranked:
        cv = r.get("cv") or {}
        ci = r.get("ci") or {}
        slim.append(
            {
                "run_id": r.get("run_id"),
                "exp_id": r.get("exp_id"),
                "model_name": r.get("model_name"),
                "pr_auc": r.get("pr_auc"),
                "roc_auc": r.get("roc_auc"),
                "f1": r.get("f1"),
                "accuracy": r.get("accuracy"),
                "threshold": r.get("threshold"),
                "cv_pr_auc_mean": cv.get("pr_auc_mean"),
                "cv_pr_auc_std": cv.get("pr_auc_std"),
                "pr_auc_ci_low": ci.get("pr_auc_low"),
                "pr_auc_ci_high": ci.get("pr_auc_high"),
                "brier": r.get("brier"),
                "calibration_method": r.get("calibration_method"),
                "ablation": r.get("ablation"),
                "includes_conversion_rate": bool(r.get("includes_conversion_rate")),
                "skipped": bool(r.get("skipped")),
                "skip_reason": r.get("skip_reason"),
            }
        )
    path = metrics_dir / "leaderboard.json"
    path.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
