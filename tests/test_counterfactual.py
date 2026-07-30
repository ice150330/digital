"""反事实解释测试：模型行为口径（敏感性分析），禁止因果措辞。"""

from __future__ import annotations

import pandas as pd
import pytest

from digital_marketing.core.paths import resolve_under_root
from digital_marketing.explain.counterfactual import (
    COUNTERFACTUAL_DISCLAIMER,
    greedy_counterfactual,
    single_feature_curve,
)
from digital_marketing.explain.pdp import compute_pdp_ice

pytestmark = pytest.mark.skipif(
    not (resolve_under_root("outputs/models") / "E2_lightgbm_default" / "model.joblib").is_file()
    or not (resolve_under_root("outputs/processed") / "test.csv").is_file(),
    reason="需先运行 scripts/06_train_full.py",
)


@pytest.fixture(scope="module")
def runtime_and_row():
    from digital_marketing.services import artifacts

    rt = artifacts.load_runtime("E2_lightgbm_default")
    test = pd.read_csv(resolve_under_root("outputs/processed/test.csv"))
    row = test.iloc[[3]].copy()
    return rt, test, row


def test_single_feature_curve_contract(runtime_and_row):
    rt, _, row = runtime_and_row
    res = single_feature_curve(
        rt["model"], rt["transformer"], row, rt["raw_feature_cols"], "TimeOnSite", grid_size=15
    )
    assert len(res["grid"]) == len(res["proba"])
    assert 0.0 <= min(res["proba"]) and max(res["proba"]) <= 1.0
    assert res["feature"] == "TimeOnSite"
    assert "不构成因果" in res["disclaimer"]


def test_greedy_counterfactual_moves_proba_up(runtime_and_row):
    rt, _, row = runtime_and_row
    numeric = [c for c in ("TimeOnSite", "AdSpend", "EmailOpens", "WebsiteVisits") if c in row.columns]
    base = rt["model"].predict_proba(rt["transformer"].transform(row[rt["raw_feature_cols"]]))[0, 1]
    target = min(0.99, float(base) + 0.2)
    res = greedy_counterfactual(
        rt["model"],
        rt["transformer"],
        row,
        rt["raw_feature_cols"],
        numeric,
        target_proba=target,
        grid_size=10,
        max_steps=4,
    )
    assert res["base_proba"] == pytest.approx(float(base), abs=1e-6)
    assert res["final_proba"] >= res["base_proba"]
    assert res["n_steps"] == len(res["steps"])
    for s in res["steps"]:
        assert s["from"] != s["to"]
    assert "不构成因果" in res["disclaimer"]
    # 文案红线：不允许出现因果承诺式措辞
    assert "提升转化" not in COUNTERFACTUAL_DISCLAIMER


def test_greedy_counterfactual_down_direction(runtime_and_row):
    rt, _, row = runtime_and_row
    numeric = [c for c in ("TimeOnSite", "AdSpend", "EmailOpens") if c in row.columns]
    res = greedy_counterfactual(
        rt["model"],
        rt["transformer"],
        row,
        rt["raw_feature_cols"],
        numeric,
        target_proba=0.01,
        grid_size=10,
        max_steps=4,
    )
    assert res["final_proba"] <= res["base_proba"]


def test_pdp_artifact_shape():
    path = resolve_under_root("outputs/explain") / "pdp_E2_lightgbm_default.json"
    if not path.is_file():
        pytest.skip("需先运行 scripts/07_explain_advanced.py")
    import json

    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["run_id"] == "E2_lightgbm_default"
    assert bundle["features"], "PDP 特征为空"
    for name, item in bundle["features"].items():
        assert len(item["grid"]) == len(item["pdp"])
        assert len(item["ice"]) <= bundle["ice_max"]
        assert "disclaimer" in item


def test_pdp_compute_on_toy(runtime_and_row):
    rt, test, _ = runtime_and_row
    res = compute_pdp_ice(
        rt["model"],
        rt["transformer"],
        test.head(60),
        rt["raw_feature_cols"],
        "AdSpend",
        grid_size=8,
        ice_max=5,
    )
    assert len(res["grid"]) == len(res["pdp"])
    assert len(res["ice"]) <= 5
    assert all(len(c["values"]) == len(res["grid"]) for c in res["ice"])
