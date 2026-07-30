"""概率校准：Platt(sigmoid) / Isotonic，valid 上 fit 与择优，test 一次评估。

红线：校准器只在 valid 上 fit；test 仅评估一次。
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, log_loss


def fit_best_calibrator(model, X_valid: np.ndarray, y_valid: np.ndarray) -> tuple[Any, str, dict[str, float]]:
    """在 valid 上分别 fit sigmoid/isotonic，按 valid Brier 择优。

    返回 (校准后模型, 方法名, valid 上两种方法的 brier 对比)。
    """
    from digital_marketing.models.metrics import _proba_positive_local

    scores: dict[str, float] = {}
    best_model = None
    best_method = "sigmoid"
    best_brier = float("inf")
    for method in ("sigmoid", "isotonic"):
        cal = CalibratedClassifierCV(model, method=method, cv="prefit")
        cal.fit(X_valid, y_valid)
        proba = _proba_positive_local(cal, X_valid)
        brier = float(brier_score_loss(y_valid, proba))
        scores[method] = brier
        if brier < best_brier:
            best_brier = brier
            best_model = cal
            best_method = method
    return best_model, best_method, scores


def _ece(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> float:
    """等频分箱 Expected Calibration Error。"""
    y_true = np.asarray(y_true, dtype=float)
    y_proba = np.asarray(y_proba, dtype=float)
    order = np.argsort(y_proba)
    y_sorted = y_true[order]
    p_sorted = y_proba[order]
    n = len(y_sorted)
    bounds = np.linspace(0, n, n_bins + 1).round().astype(int)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = int(bounds[i]), int(bounds[i + 1])
        if hi <= lo:
            continue
        gap = abs(float(p_sorted[lo:hi].mean()) - float(y_sorted[lo:hi].mean()))
        ece += (hi - lo) / n * gap
    return float(ece)


def _calibration_bins(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> list[dict[str, Any]]:
    y_true = np.asarray(y_true, dtype=float)
    y_proba = np.asarray(y_proba, dtype=float)
    order = np.argsort(y_proba)
    y_sorted = y_true[order]
    p_sorted = y_proba[order]
    n = len(y_sorted)
    bounds = np.linspace(0, n, n_bins + 1).round().astype(int)
    bins: list[dict[str, Any]] = []
    for i in range(n_bins):
        lo, hi = int(bounds[i]), int(bounds[i + 1])
        if hi <= lo:
            continue
        bins.append(
            {
                "bin": i + 1,
                "count": int(hi - lo),
                "mean_pred": float(p_sorted[lo:hi].mean()),
                "frac_pos": float(y_sorted[lo:hi].mean()),
            }
        )
    return bins


def calibration_side(
    y_true: np.ndarray, y_proba: np.ndarray, *, n_bins: int = 10
) -> dict[str, Any]:
    """单侧（校准前或后）的校准统计：brier / log_loss / ece / 分箱点。"""
    y_true = np.asarray(y_true)
    y_proba = np.clip(np.asarray(y_proba, dtype=float), 1e-7, 1 - 1e-7)
    return {
        "brier": float(brier_score_loss(y_true, y_proba)),
        "log_loss": float(log_loss(y_true, y_proba, labels=[0, 1])),
        "ece": _ece(y_true, y_proba, n_bins=n_bins),
        "bins": _calibration_bins(y_true, y_proba, n_bins=n_bins),
    }


def calibration_report(
    y_test: np.ndarray,
    proba_before: np.ndarray,
    proba_after: np.ndarray,
    *,
    method: str,
    valid_brier_compare: dict[str, float] | None = None,
) -> dict[str, Any]:
    """test 上校准前后对比（test 仅评估，不参与 fit）。"""
    return {
        "method": method,
        "valid_brier_compare": valid_brier_compare or {},
        "before": calibration_side(y_test, proba_before),
        "after": calibration_side(y_test, proba_after),
        "note": "校准器仅在 valid 上 fit；test 一次评估",
    }
