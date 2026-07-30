"""预算分配模拟器测试：期望值口径、排序与推荐 K 的正确性。"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from digital_marketing.core.paths import resolve_under_root
from digital_marketing.simulate.budget import (
    SIMULATE_DISCLAIMER,
    expected_value_curve,
    reach_list,
)


def _toy_proba() -> np.ndarray:
    # 前 5 个高概率、后 5 个低概率，便于断言排序行为
    return np.array([0.95, 0.9, 0.8, 0.7, 0.6, 0.3, 0.2, 0.1, 0.05, 0.01])


def test_curve_monotone_and_disclaimer():
    proba = _toy_proba()
    res = expected_value_curve(proba, value_per_conversion=10.0, cost_per_contact=4.0)
    ks = [c["k"] for c in res["curve"]]
    assert ks == sorted(ks) and len(set(ks)) == len(ks)
    convs = [c["expected_conversions"] for c in res["curve"]]
    assert all(b >= a for a, b in zip(convs, convs[1:]))  # 累计期望转化单调不减
    assert "非因果" in res["disclaimer"] or "不构成" in res["disclaimer"]
    assert res["params"]["value_per_conversion"] == 10.0
    assert res["params"]["cost_per_contact"] == 4.0


def test_recommended_k_is_argmax_positive_net():
    proba = _toy_proba()
    res = expected_value_curve(proba, value_per_conversion=10.0, cost_per_contact=4.0)
    nets = [c["expected_net"] for c in res["curve"]]
    best = res["recommended"]
    assert best is not None
    assert best["expected_net"] == max(nets)
    # 期望价值 = p*10-4：p=0.3 → -1 不值得；前 5 个值得
    assert res["recommended_k"] == 5


def test_budget_cap_limits_k():
    proba = _toy_proba()
    res = expected_value_curve(
        proba, value_per_conversion=10.0, cost_per_contact=4.0, budget=12.0
    )
    assert max(c["k"] for c in res["curve"]) <= 3  # 12/4=3
    with pytest.raises(ValueError):
        expected_value_curve(proba, value_per_conversion=10.0, cost_per_contact=4.0, budget=1.0)


def test_invalid_params_rejected():
    with pytest.raises(ValueError):
        expected_value_curve(_toy_proba(), value_per_conversion=0, cost_per_contact=4.0)
    with pytest.raises(ValueError):
        expected_value_curve(_toy_proba(), value_per_conversion=10.0, cost_per_contact=-1.0)


def test_reach_list_shape_and_order():
    proba = _toy_proba()
    df = pd.DataFrame({"CustomerID": range(100, 110)})
    names = reach_list(df, proba, k=4, value_per_conversion=10.0, cost_per_contact=4.0)
    assert len(names) == 4
    assert list(names["rank"]) == [1, 2, 3, 4]
    probs = list(names["proba"])
    assert probs == sorted(probs, reverse=True)
    assert list(names["customerid"]) == [100, 101, 102, 103]


@pytest.mark.skipif(
    not (resolve_under_root("outputs/simulate") / "budget_curve_E2_lightgbm_default.json").is_file(),
    reason="需先运行 scripts/08_simulate_budget.py",
)
def test_precomputed_artifact_contract():
    path = resolve_under_root("outputs/simulate") / "budget_curve_E2_lightgbm_default.json"
    res = json.loads(path.read_text(encoding="utf-8"))
    for key in ("params", "curve", "recommended_k", "recommended", "disclaimer", "run_id"):
        assert key in res
    assert 0 < res["recommended_k"] <= res["n_population"]
    assert SIMULATE_DISCLAIMER[:10] in res["disclaimer"]
    reach = resolve_under_root("outputs/simulate") / f"reach_list_{res['run_id']}.csv"
    assert reach.is_file()
