"""分类指标：PR-AUC 主指标；阈值在 valid 搜、test 一次评估。"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)


def pr_auc(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    return float(average_precision_score(y_true, y_proba))


def roc_auc_safe(y_true: np.ndarray, y_proba: np.ndarray) -> float | None:
    try:
        return float(roc_auc_score(y_true, y_proba))
    except ValueError:
        return None


def search_threshold_f1(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    *,
    start: float = 0.05,
    stop: float = 0.95,
    step: float = 0.01,
) -> tuple[float, float]:
    """在 valid 上按 F1 搜阈值，返回 (best_threshold, best_f1)。"""
    best_t, best_f1 = 0.5, -1.0
    t = start
    while t <= stop + 1e-12:
        pred = (y_proba >= t).astype(int)
        f1 = float(f1_score(y_true, pred, zero_division=0))
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)
        t += step
    return best_t, best_f1


def evaluate_at_threshold(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    pred = (y_proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, pred, average="binary", zero_division=0
    )
    return {
        "threshold": float(threshold),
        "pr_auc": pr_auc(y_true, y_proba),
        "roc_auc": roc_auc_safe(y_true, y_proba),
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "accuracy": float(accuracy_score(y_true, pred)),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }
