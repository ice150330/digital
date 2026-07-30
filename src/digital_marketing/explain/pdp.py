"""PDP / ICE：在原始特征空间做扰动（其余特征保持观测值），test 集口径。

说明：PDP/ICE 描述「模型预测随特征取值如何变化」，是模型行为分析，
不构成因果效应估计（特征间相关性会使反事实行偏离真实数据流形）。
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from digital_marketing.models.classify import _predict_proba_positive

PDP_DISCLAIMER = "PDP/ICE 反映模型预测对特征取值的响应，不等于因果效应。"


def feature_grid(series: pd.Series, grid_size: int = 40) -> np.ndarray:
    """数值特征网格：分位数点去重；类别/低基数特征退化为唯一取值（≤grid_size）。"""
    s = pd.to_numeric(series, errors="coerce").dropna()
    uniq = np.unique(s.to_numpy())
    if uniq.size <= grid_size:
        return uniq
    qs = np.linspace(0.0, 1.0, grid_size)
    grid = np.unique(np.quantile(uniq, qs))
    return grid


def compute_pdp_ice(
    model,
    transformer,
    df: pd.DataFrame,
    raw_cols: list[str],
    feature: str,
    *,
    grid_size: int = 40,
    ice_max: int = 50,
    seed: int = 42,
) -> dict[str, Any]:
    """单特征 PDP + ICE（抽样 ice_max 行）。

    df：评估用原始行（建议 test）；raw_cols：transformer 期望的原始特征列。
    """
    if feature not in df.columns:
        raise ValueError(f"特征不存在: {feature}")
    grid = feature_grid(df[feature], grid_size=grid_size)
    rng = np.random.default_rng(seed)
    ice_idx = rng.choice(len(df), size=min(ice_max, len(df)), replace=False)
    ice_idx_set = set(int(i) for i in ice_idx)

    pdp_values: list[float] = []
    ice_curves: dict[int, list[float]] = {i: [] for i in sorted(ice_idx_set)}
    base = df.copy()
    for v in grid:
        perturbed = base.copy()
        perturbed[feature] = float(v)
        X = transformer.transform(perturbed[raw_cols])
        proba = _predict_proba_positive(model, X)
        pdp_values.append(float(np.mean(proba)))
        for i in ice_curves:
            ice_curves[i].append(float(proba[i]))

    return {
        "feature": feature,
        "grid": [float(v) for v in grid],
        "pdp": pdp_values,
        "ice": [{"index": i, "values": vals} for i, vals in ice_curves.items()],
        "n_samples": int(len(df)),
        "y_kind": "proba",
        "disclaimer": PDP_DISCLAIMER,
    }


def compute_pdp_bundle(
    model,
    transformer,
    df: pd.DataFrame,
    raw_cols: list[str],
    features: list[str],
    *,
    run_id: str,
    grid_size: int = 40,
    ice_max: int = 50,
    seed: int = 42,
) -> dict[str, Any]:
    """多特征 PDP 打包落盘结构。"""
    out: dict[str, Any] = {
        "run_id": run_id,
        "features": {},
        "grid_size": grid_size,
        "ice_max": ice_max,
        "disclaimer": PDP_DISCLAIMER,
    }
    for f in features:
        out["features"][f] = compute_pdp_ice(
            model,
            transformer,
            df,
            raw_cols,
            f,
            grid_size=grid_size,
            ice_max=ice_max,
            seed=seed,
        )
    return out
