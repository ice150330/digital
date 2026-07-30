"""单样本局部贡献。"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from digital_marketing.explain.global_shap import _coef_proxy, _lgbm_contrib, _shap_tree_values

logger = logging.getLogger(__name__)


def compute_local_shap(
    model,
    x_row: np.ndarray,
    feature_names: list[str],
    feature_values: list[Any] | None = None,
    *,
    background: np.ndarray | None = None,
    top_k: int = 10,
) -> dict[str, Any]:
    """解释单行（已变换特征）。"""
    X = np.asarray(x_row, dtype=float).reshape(1, -1)
    method = "unknown"
    sv = _lgbm_contrib(model, X)
    if sv is not None:
        method = "lightgbm_pred_contrib"
        contrib = sv.reshape(-1)
    else:
        # TreeExplainer 可用 background 但这里直接对单行
        batch = X if background is None else np.vstack([background[:30], X])
        tree_sv = _shap_tree_values(model, batch)
        if tree_sv is not None:
            method = "shap_tree"
            contrib = np.asarray(tree_sv[-1]).reshape(-1)
        else:
            proxy = _coef_proxy(model, X)
            if proxy is not None:
                method = "linear_coef_proxy"
                contrib = proxy.reshape(-1)
            else:
                method = "zero_fallback"
                contrib = np.zeros(X.shape[1], dtype=float)

    values = feature_values
    if values is None:
        values = [float(v) for v in X.reshape(-1)]

    pairs: list[dict[str, Any]] = []
    for i, name in enumerate(feature_names):
        if i >= len(contrib):
            break
        fv = values[i] if i < len(values) else None
        if isinstance(fv, (float, np.floating)):
            fv = float(fv)
        pairs.append(
            {
                "name": name,
                "feature_value": fv,
                "shap_value": float(contrib[i]),
            }
        )
    pairs.sort(key=lambda p: abs(p["shap_value"]), reverse=True)
    return {"method": method, "top_features": pairs[:top_k]}
