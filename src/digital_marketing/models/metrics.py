"""分类指标：PR-AUC 主指标；阈值在 valid 搜、test 一次评估。

阶段9 扩展：5-fold CV 汇总、bootstrap CI、PR/ROC 曲线点、
lift 十分位表、成本敏感阈值扫描 —— 均为「评估统计」，不重训模型。
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
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


# ---------------------------------------------------------------------------
# 阶段9：增强评估统计
# ---------------------------------------------------------------------------


def _thin(xs: np.ndarray, max_points: int) -> np.ndarray:
    """等距抽稀到 max_points 以内，保留端点。"""
    xs = np.asarray(xs, dtype=float)
    n = xs.shape[0]
    if n <= max_points:
        return xs
    idx = np.unique(np.linspace(0, n - 1, max_points).round().astype(int))
    return xs[idx]


def bootstrap_pr_auc_ci(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    *,
    n_boot: int = 1000,
    level: float = 0.95,
    seed: int = 42,
) -> dict[str, Any]:
    """对 test 预测做 bootstrap 重采样，估计 PR-AUC 置信区间（不重训模型）。"""
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba, dtype=float)
    n = y_true.shape[0]
    rng = np.random.default_rng(seed)
    stats: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if y_true[idx].sum() == 0:
            continue  # 重采样样本无正类，跳过
        stats.append(average_precision_score(y_true[idx], y_proba[idx]))
    if not stats:
        return {"pr_auc_low": None, "pr_auc_high": None, "n_boot": n_boot, "level": level}
    alpha = (1.0 - level) / 2.0
    low, high = np.quantile(np.asarray(stats), [alpha, 1.0 - alpha])
    return {
        "pr_auc_low": float(low),
        "pr_auc_high": float(high),
        "n_boot": n_boot,
        "level": level,
        "note": "test 预测 bootstrap，不重训",
    }


def pr_curve_points(
    y_true: np.ndarray, y_proba: np.ndarray, *, max_points: int = 200
) -> dict[str, Any]:
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    idx_n = min(precision.shape[0], max_points)
    # 统一抽稀（precision/recall 等长）
    p = _thin(precision, idx_n) if precision.shape[0] > max_points else precision
    r = _thin(recall, idx_n) if recall.shape[0] > max_points else recall
    return {
        "precision": [float(x) for x in np.asarray(p)],
        "recall": [float(x) for x in np.asarray(r)],
        "n_points": int(len(np.asarray(p))),
    }


def roc_curve_points(
    y_true: np.ndarray, y_proba: np.ndarray, *, max_points: int = 200
) -> dict[str, Any]:
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    if fpr.shape[0] > max_points:
        idx = np.unique(np.linspace(0, fpr.shape[0] - 1, max_points).round().astype(int))
        fpr, tpr = fpr[idx], tpr[idx]
    return {
        "fpr": [float(x) for x in fpr],
        "tpr": [float(x) for x in tpr],
        "n_points": int(len(fpr)),
    }


def lift_deciles(y_true: np.ndarray, y_proba: np.ndarray, *, n_bins: int = 10) -> list[dict[str, Any]]:
    """按预测概率降序切 n_bins 组，输出累计捕获率与 lift（营销标准升降表）。"""
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba, dtype=float)
    order = np.argsort(-y_proba)
    y_sorted = y_true[order]
    n = len(y_sorted)
    total_pos = float(y_sorted.sum()) or 1.0
    base_rate = float(y_true.mean()) or 1e-12
    rows: list[dict[str, Any]] = []
    cum_pos = 0.0
    cum_n = 0
    # 等频切分
    bounds = np.linspace(0, n, n_bins + 1).round().astype(int)
    for i in range(n_bins):
        lo, hi = int(bounds[i]), int(bounds[i + 1])
        seg = y_sorted[lo:hi]
        cum_pos += float(seg.sum())
        cum_n += int(hi - lo)
        capture = cum_pos / total_pos
        rows.append(
            {
                "decile": i + 1,
                "n": int(hi - lo),
                "positives": int(seg.sum()),
                "cum_n": cum_n,
                "capture_rate": float(capture),
                "lift": float((cum_pos / max(cum_n, 1)) / base_rate),
            }
        )
    return rows


def threshold_scan(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    *,
    cost_fp: float = 1.0,
    cost_fn: float = 5.0,
    start: float = 0.05,
    stop: float = 0.95,
    step: float = 0.01,
) -> dict[str, Any]:
    """阈值 × {precision, recall, f1, expected_cost} 扫描；期望成本 = FP*cost_fp + FN*cost_fn。"""
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba, dtype=float)
    rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    t = start
    while t <= stop + 1e-12:
        pred = (y_proba >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, pred, average="binary", zero_division=0
        )
        cost = float(fp) * cost_fp + float(fn) * cost_fn
        row = {
            "threshold": float(round(t, 4)),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "expected_cost": cost,
        }
        rows.append(row)
        if best is None or cost < best["expected_cost"]:
            best = row
        t += step
    return {
        "cost_fp": float(cost_fp),
        "cost_fn": float(cost_fn),
        "cost_note": "期望成本 = FP×cost_fp + FN×cost_fn（test 集计数，相对比较口径）",
        "rows": rows,
        "best_by_cost": best,
    }


def cv_pr_auc_summary(
    estimator_factory,
    X: np.ndarray,
    y: np.ndarray,
    *,
    folds: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """StratifiedKFold（仅 train）逐折 PR-AUC 的均值/标准差。

    estimator_factory: 无参可调用，返回未 fit 的估计器（保证每折独立实例）。
    """
    from sklearn.model_selection import StratifiedKFold

    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    scores: list[float] = []
    for tr_idx, va_idx in skf.split(X, y):
        est = estimator_factory()
        est.fit(X[tr_idx], y[tr_idx])
        proba = _proba_positive_local(est, X[va_idx])
        scores.append(average_precision_score(y[va_idx], proba))
    arr = np.asarray(scores, dtype=float)
    return {
        "pr_auc_mean": float(arr.mean()),
        "pr_auc_std": float(arr.std(ddof=0)),
        "folds": int(folds),
        "note": "StratifiedKFold 仅 train；fold 间 PR-AUC 离散度",
    }


def _proba_positive_local(model, X: np.ndarray) -> np.ndarray:
    """与 classify._predict_proba_positive 同逻辑（避免环依赖的本地副本）。"""
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        if proba.shape[1] == 1:
            classes = list(getattr(model, "classes_", [1]))
            return proba[:, 0] if classes[0] == 1 else 1.0 - proba[:, 0]
        classes = list(model.classes_)
        if 1 in classes:
            return proba[:, classes.index(1)]
        return proba[:, -1]
    pred = model.predict(X)
    return pred.astype(float)
