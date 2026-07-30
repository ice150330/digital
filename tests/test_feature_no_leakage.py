"""特征无泄漏与 CustomerID 红线。"""

from __future__ import annotations

from digital_marketing.features.schema import assert_no_leakage, load_feature_config


def test_feature_config_excludes_customer_id_and_label():
    cfg = load_feature_config()
    cols = cfg.feature_columns()
    assert "CustomerID" not in cols
    assert "Conversion" not in cols
    assert cfg.target == "Conversion"
    assert_no_leakage(cols)


def test_conversion_rate_not_in_default_features():
    cfg = load_feature_config()
    assert "ConversionRate" not in cfg.feature_columns()
    assert "ConversionRate" in (cfg.drop_features or []) or "ConversionRate" in (
        cfg.never_features or []
    )


def test_assert_no_leakage_raises():
    try:
        assert_no_leakage(["Age", "CustomerID"])
        raised = False
    except ValueError:
        raised = True
    assert raised
