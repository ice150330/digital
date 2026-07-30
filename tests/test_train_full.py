"""阶段9 W9a：全量训练矩阵与增强评估的产物契约测试。

依赖 outputs/ 已跑过 scripts/06_train_full.py 的产物；
若产物缺失则跳过（CI 轻量环境下不强行重训）。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from digital_marketing.core.paths import resolve_under_root
from digital_marketing.services import artifacts

FULL_RUNS = [
    "E0_dummy_majority",
    "E1_logistic_balanced",
    "E2_lightgbm_default",
    "E3_lightgbm_balanced",
    "E4_lightgbm_smote",
    "E5_lightgbm_plus_conversionrate",
    "E6_lightgbm_no_quality_flags",
    "E7_stacking_lgbm_rf_lr",
    "E8_lightgbm_calibrated",
]


def _metrics_path(run_id: str) -> Path:
    return resolve_under_root("outputs/metrics") / f"{run_id}.json"


def _has_full_artifacts() -> bool:
    return all(_metrics_path(r).is_file() for r in FULL_RUNS)


pytestmark = pytest.mark.skipif(not _has_full_artifacts(), reason="需先运行 scripts/06_train_full.py")


def test_enhanced_fields_present():
    """每个 run 的 metrics 都带 CV / CI / 曲线 / lift / 阈值扫描。"""
    for run_id in FULL_RUNS:
        m = json.loads(_metrics_path(run_id).read_text(encoding="utf-8"))
        for key in ("cv", "ci", "pr_curve", "roc_curve", "lift_deciles", "threshold_scan"):
            assert key in m, f"{run_id} 缺 {key}"
        assert m["cv"]["folds"] == 5
        assert m["ci"]["n_boot"] == 1000
        assert len(m["lift_deciles"]) == 10


def test_ci_contains_point_estimate():
    """bootstrap CI 应包含 test 点估计（宽松容差）。"""
    for run_id in FULL_RUNS:
        m = json.loads(_metrics_path(run_id).read_text(encoding="utf-8"))
        low, high, point = m["ci"]["pr_auc_low"], m["ci"]["pr_auc_high"], m["pr_auc"]
        assert low is not None and high is not None
        assert low <= point + 0.01 and high >= point - 0.01, f"{run_id} CI 不含点估计"


def test_lift_first_decile_capture():
    """升降表第一十分位捕获率应显著高于随机（>10% 且 lift>1）。"""
    m = json.loads(_metrics_path("E2_lightgbm_default").read_text(encoding="utf-8"))
    first = m["lift_deciles"][0]
    assert first["capture_rate"] > 0.10
    assert first["lift"] > 1.0


def test_calibration_artifact_and_improvement():
    """E8 校准产物存在；isotonic/platt 择优后 ECE 不劣于校准前。"""
    path = resolve_under_root("outputs/metrics") / "calibration_E8_lightgbm_calibrated.json"
    assert path.is_file()
    c = json.loads(path.read_text(encoding="utf-8"))
    assert c["method"] in ("sigmoid", "isotonic")
    for side in ("before", "after"):
        assert {"brier", "log_loss", "ece", "bins"} <= set(c[side])
    assert c["after"]["ece"] <= c["before"]["ece"] + 1e-9


def test_e5_marked_ablation_and_excluded_from_default():
    """E5 泄漏消融：meta 打标 + 永不被选为默认 run。"""
    meta = json.loads(
        (resolve_under_root("outputs/models") / "E5_lightgbm_plus_conversionrate" / "meta.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["includes_conversion_rate"] is True
    assert meta["ablation"] == "conversion_rate"
    assert "ConversionRate" in meta["feature_schema"]["feature_columns_raw"]
    assert (resolve_under_root("outputs/models") / "E5_lightgbm_plus_conversionrate" / "transformer.joblib").is_file()
    assert artifacts.pick_default_run_id() != "E5_lightgbm_plus_conversionrate"
    # 默认 run 必须是非消融 run
    default_meta = json.loads(
        (resolve_under_root("outputs/models") / artifacts.pick_default_run_id() / "meta.json").read_text(
            encoding="utf-8"
        )
    )
    assert not default_meta.get("includes_conversion_rate")
    assert not default_meta.get("ablation")


def test_per_run_transformer_loaded():
    """E5/E6 变体 run 的 load_runtime 应使用 run 目录 transformer 与变体特征列。"""
    rt = artifacts.load_runtime("E5_lightgbm_plus_conversionrate")
    assert "ConversionRate" in rt["raw_feature_cols"]
    rt6 = artifacts.load_runtime("E6_lightgbm_no_quality_flags")
    assert "email_inconsistent" not in rt6["raw_feature_cols"]


def test_stacking_predicts():
    """E7 stacking 模型可 predict_proba 且概率在 [0,1]。"""
    import numpy as np

    rt = artifacts.load_runtime("E7_stacking_lgbm_rf_lr")
    train = __import__("pandas").read_csv(resolve_under_root("outputs/processed/train.csv"))
    X = rt["transformer"].transform(train[rt["raw_feature_cols"]].iloc[:5])
    proba = rt["model"].predict_proba(X)[:, 1]
    assert np.all((proba >= 0) & (proba <= 1))
