"""预算分配模拟器：按「期望价值 = 校准概率 × 单客价值 − 触达成本」排序触达。

红线口径：全部为模型期望值（期望转化数 / 期望净收益），
基于 test 集历史预测，不构成因果 uplift，也不构成实际收益承诺。
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

SIMULATE_DISCLAIMER = (
    "以下为模型期望值模拟（概率 × 价值 − 成本），基于历史 test 集预测排序；"
    "不构成因果 uplift 或实际投放收益承诺。"
)

# 默认口径：盈亏平衡 proba = cost/value = 0.4；
# 本数据正类率 ~87.65% 概率整体偏高，比率 2.5 时曲线才有内点最优（可演示排序价值）
DEFAULT_VALUE_PER_CONVERSION = 10.0
DEFAULT_COST_PER_CONTACT = 4.0


def expected_value_curve(
    proba: np.ndarray,
    *,
    value_per_conversion: float = DEFAULT_VALUE_PER_CONVERSION,
    cost_per_contact: float = DEFAULT_COST_PER_CONTACT,
    budget: float | None = None,
    n_points: int = 25,
) -> dict[str, Any]:
    """按期望价值降序触达，扫描触达人数 K → 期望转化/期望净收益曲线。

    budget：给定则 K 上限 = floor(budget / cost_per_contact)。
    返回曲线 + 推荐 K（期望净收益最大且为正）。
    """
    proba = np.asarray(proba, dtype=float)
    n = proba.shape[0]
    value = float(value_per_conversion)
    cost = float(cost_per_contact)
    if cost <= 0 or value <= 0:
        raise ValueError("value_per_conversion 与 cost_per_contact 必须为正")

    # 期望价值排序（同分时概率高者优先，确定性）
    order = np.lexsort((-proba, -(proba * value - cost)))
    sorted_proba = proba[order]

    max_k = n
    if budget is not None:
        max_k = min(n, int(float(budget) // cost))
    if max_k < 1:
        raise ValueError("预算不足以触达任何客户")

    ks = np.unique(np.linspace(1, max_k, min(n_points, max_k)).round().astype(int))
    cum_proba = np.cumsum(sorted_proba)
    curve: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for k in ks:
        k = int(k)
        exp_conv = float(cum_proba[k - 1])
        exp_net = exp_conv * value - k * cost
        row = {
            "k": k,
            "expected_conversions": exp_conv,
            "expected_net": float(exp_net),
            "expected_revenue": float(exp_conv * value),
            "budget_used": float(k * cost),
            "avg_proba": float(sorted_proba[:k].mean()),
        }
        curve.append(row)
        if exp_net > 0 and (best is None or exp_net > best["expected_net"]):
            best = row

    return {
        "params": {
            "value_per_conversion": value,
            "cost_per_contact": cost,
            "budget": float(budget) if budget is not None else None,
        },
        "n_population": n,
        "curve": curve,
        "recommended_k": int(best["k"]) if best else 0,
        "recommended": best,
        "disclaimer": SIMULATE_DISCLAIMER,
    }


def reach_list(
    df: pd.DataFrame,
    proba: np.ndarray,
    *,
    k: int,
    value_per_conversion: float = DEFAULT_VALUE_PER_CONVERSION,
    cost_per_contact: float = DEFAULT_COST_PER_CONTACT,
    id_column: str = "CustomerID",
) -> pd.DataFrame:
    """Top-K 触达名单：customer_id + proba + 期望价值，供导出 CSV。"""
    proba = np.asarray(proba, dtype=float)
    ev = proba * float(value_per_conversion) - float(cost_per_contact)
    order = np.lexsort((-proba, -ev))
    k = max(0, min(int(k), len(order)))
    out = pd.DataFrame(
        {
            "rank": np.arange(1, k + 1),
            "proba": proba[order[:k]],
            "expected_value": ev[order[:k]],
        }
    )
    if id_column in df.columns:
        out.insert(1, id_column.lower(), df[id_column].to_numpy()[order[:k]])
    return out
