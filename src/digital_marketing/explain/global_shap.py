"""全局特征贡献：优先原生 contrib / TreeExplainer，失败则回退。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from digital_marketing.core.paths import ensure_dir

logger = logging.getLogger(__name__)


def _top_from_mean_abs(
    mean_abs: np.ndarray,
    feature_names: list[str],
    top_k: int,
) -> list[dict[str, Any]]:
    order = np.argsort(-mean_abs)[:top_k]
    out = []
    for i in order:
        name = feature_names[i] if i < len(feature_names) else f"f{int(i)}"
        out.append({"name": name, "mean_abs_shap": float(mean_abs[i])})
    return out


def _lgbm_contrib(model, X: np.ndarray) -> np.ndarray | None:
    """LightGBM pred_contrib → (n, n_features)，去掉 bias 列。"""
    try:
        booster = getattr(model, "booster_", None)
        if booster is None and hasattr(model, "predict"):
            # LGBMClassifier
            raw = model.predict(X, pred_contrib=True)
        elif booster is not None:
            raw = booster.predict(X, pred_contrib=True)
        else:
            return None
        arr = np.asarray(raw)
        if arr.ndim != 2 or arr.shape[1] < 2:
            return None
        return arr[:, :-1]  # 最后一列为 expected value
    except Exception as e:  # noqa: BLE001
        logger.debug("lgbm contrib 失败: %s", e)
        return None


def _shap_tree_values(model, X: np.ndarray) -> np.ndarray | None:
    # 当前环境 shap→matplotlib 与 NumPy2 可能冲突；失败则静默回退
    try:
        import os

        os.environ.setdefault("MPLBACKEND", "Agg")
        # 仅树模型尝试，避免 Logistic 无意义报错
        name = type(model).__name__.lower()
        if not any(k in name for k in ("lgbm", "forest", "tree", "xgb", "boost")):
            return None
        import shap  # noqa: WPS433

        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        if isinstance(sv, list):
            sv = sv[1] if len(sv) > 1 else sv[0]
        sv = np.asarray(sv)
        if sv.ndim == 3:
            sv = sv[:, :, -1]
        return sv
    except BaseException as e:  # noqa: BLE001 — 含 numpy/matplotlib 二进制不兼容
        logger.warning("TreeExplainer 不可用: %s", e)
        return None


def _coef_proxy(model, X: np.ndarray) -> np.ndarray | None:
    """线性模型：|coef * x| 作为局部贡献代理（非严格 SHAP）。"""
    coef = getattr(model, "coef_", None)
    if coef is None:
        return None
    w = np.asarray(coef).reshape(-1)
    if w.size != X.shape[1]:
        return None
    return X * w.reshape(1, -1)


def _permutation_importance_proxy(model, X: np.ndarray, y: np.ndarray | None) -> np.ndarray | None:
    """无 y 时用 predict_proba 方差扰动近似全局重要性。"""
    try:
        from sklearn.inspection import permutation_importance

        if y is None:
            return None
        if not hasattr(model, "predict"):
            return None
        r = permutation_importance(model, X, y, n_repeats=3, random_state=42, scoring=None)
        return np.asarray(r.importances_mean, dtype=float)
    except Exception as e:  # noqa: BLE001
        logger.debug("permutation 失败: %s", e)
        return None


def compute_global_shap(
    model,
    X: np.ndarray,
    feature_names: list[str],
    *,
    y: np.ndarray | None = None,
    max_samples: int = 200,
    top_k: int = 15,
    seed: int = 42,
) -> dict[str, Any]:
    """计算全局 Top-K 重要性。"""
    n = X.shape[0]
    rng = np.random.default_rng(seed)
    if n > max_samples:
        idx = rng.choice(n, size=max_samples, replace=False)
        Xs = X[idx]
        ys = y[idx] if y is not None else None
    else:
        Xs = X
        ys = y

    method = "unknown"
    sv = _lgbm_contrib(model, Xs)
    if sv is not None:
        method = "lightgbm_pred_contrib"
        mean_abs = np.mean(np.abs(sv), axis=0)
    else:
        sv = _shap_tree_values(model, Xs)
        if sv is not None:
            method = "shap_tree"
            mean_abs = np.mean(np.abs(sv), axis=0)
        else:
            sv = _coef_proxy(model, Xs)
            if sv is not None:
                method = "linear_coef_proxy"
                mean_abs = np.mean(np.abs(sv), axis=0)
            else:
                mean_abs = _permutation_importance_proxy(model, Xs, ys)
                if mean_abs is None:
                    # 最后回退：特征方差（仅占位，标注 method）
                    method = "feature_std_fallback"
                    mean_abs = np.std(Xs, axis=0)
                else:
                    method = "permutation_importance"

    top_features = _top_from_mean_abs(np.asarray(mean_abs).reshape(-1), feature_names, top_k)
    return {
        "method": method,
        "n_samples": int(Xs.shape[0]),
        "top_features": top_features,
    }


def save_global_shap(payload: dict[str, Any], explain_dir: Path, run_id: str) -> Path:
    explain_dir = ensure_dir(Path(explain_dir))
    path = explain_dir / f"global_{run_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
