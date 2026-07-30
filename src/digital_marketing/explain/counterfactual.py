"""反事实解释（模型行为口径）：单特征扰动曲线 + 贪心多特征最小改动搜索。

红线口径：所有输出必须带 COUNTERFACTUAL_DISCLAIMER；禁止「提升转化」式因果措辞，
只能说「模型预测概率变化」。
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from digital_marketing.explain.pdp import feature_grid
from digital_marketing.models.classify import _predict_proba_positive

COUNTERFACTUAL_DISCLAIMER = (
    "以下反事实仅描述模型在该样本邻域的预测行为（敏感性分析），"
    "不构成因果效应，也不构成实际投放建议；特征间相关性可能使扰动行偏离真实客群。"
)


def _proba_of_row(model, transformer, row_df: pd.DataFrame, raw_cols: list[str]) -> float:
    X = transformer.transform(row_df[raw_cols])
    return float(_predict_proba_positive(model, X)[0])


def single_feature_curve(
    model,
    transformer,
    row_df: pd.DataFrame,
    raw_cols: list[str],
    feature: str,
    *,
    grid_size: int = 25,
) -> dict[str, Any]:
    """固定其余特征，扫单特征网格，返回模型预测概率曲线。"""
    if feature not in row_df.columns:
        raise ValueError(f"特征不存在: {feature}")
    grid = feature_grid(row_df[feature], grid_size=grid_size)
    base_value = float(pd.to_numeric(row_df[feature].iloc[0], errors="coerce"))
    probas: list[float] = []
    for v in grid:
        perturbed = row_df.copy()
        perturbed[feature] = float(v)
        probas.append(_proba_of_row(model, transformer, perturbed, raw_cols))
    base_proba = _proba_of_row(model, transformer, row_df, raw_cols)
    return {
        "feature": feature,
        "base_value": base_value,
        "base_proba": base_proba,
        "grid": [float(v) for v in grid],
        "proba": probas,
        "disclaimer": COUNTERFACTUAL_DISCLAIMER,
    }


def greedy_counterfactual(
    model,
    transformer,
    row_df: pd.DataFrame,
    raw_cols: list[str],
    numeric_features: list[str],
    *,
    target_proba: float,
    grid_size: int = 15,
    max_steps: int = 8,
    tol: float = 1e-4,
) -> dict[str, Any]:
    """贪心搜索达 target_proba 的最小改动路径。

    每步在所有候选数值特征的网格上找「使 proba 最接近 target」的单点改动，
    直到达标或步数耗尽。返回逐步路径（feature, from, to, proba_after）。
    """
    target = float(np.clip(target_proba, 0.0, 1.0))
    current = row_df.copy()
    base_proba = _proba_of_row(model, transformer, current, raw_cols)
    cur_proba = base_proba
    steps: list[dict[str, Any]] = []
    # 已经调过的特征不重复调（保证“最小改动”语义）
    used: set[str] = set()
    direction = 1.0 if target > cur_proba else -1.0

    for _ in range(max_steps):
        if (direction > 0 and cur_proba >= target - tol) or (direction < 0 and cur_proba <= target + tol):
            break
        best: dict[str, Any] | None = None
        for feat in numeric_features:
            if feat in used or feat not in current.columns:
                continue
            cur_val = pd.to_numeric(current[feat].iloc[0], errors="coerce")
            if pd.isna(cur_val):
                continue
            for v in feature_grid(current[feat], grid_size=grid_size):
                if float(v) == float(cur_val):
                    continue
                # 方向过滤：只接受朝目标前进的改动
                perturbed = current.copy()
                perturbed[feat] = float(v)
                p = _proba_of_row(model, transformer, perturbed, raw_cols)
                gain = (p - cur_proba) * direction
                if gain <= 0:
                    continue
                dist = abs(target - p)
                key = (dist, -gain)
                if best is None or key < best["_key"]:
                    best = {
                        "_key": key,
                        "feature": feat,
                        "from": float(cur_val),
                        "to": float(v),
                        "proba_after": float(p),
                    }
        if best is None:
            break
        current = current.copy()
        current[best["feature"]] = best["to"]
        cur_proba = best["proba_after"]
        used.add(best["feature"])
        steps.append(
            {
                "feature": best["feature"],
                "from": best["from"],
                "to": best["to"],
                "proba_after": best["proba_after"],
            }
        )

    achieved = (direction > 0 and cur_proba >= target - tol) or (
        direction < 0 and cur_proba <= target + tol
    )
    return {
        "base_proba": float(base_proba),
        "target_proba": target,
        "final_proba": float(cur_proba),
        "achieved": bool(achieved),
        "n_steps": len(steps),
        "steps": steps,
        "disclaimer": COUNTERFACTUAL_DISCLAIMER,
    }
