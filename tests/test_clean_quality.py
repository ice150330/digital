"""清洗 / 质量 / split 测试。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from digital_marketing.data.clean import add_quality_flags, clean_dataframe, save_clean
from digital_marketing.data.load import load_raw_csv
from digital_marketing.data.quality import profile_dataframe
from digital_marketing.data.split import stratified_three_way_split
from digital_marketing.features.schema import assert_no_leakage, load_feature_config


def test_quality_flags_on_sample(sample_csv: Path) -> None:
    df = load_raw_csv(sample_csv)
    cleaned = clean_dataframe(df)
    assert "email_inconsistent" in cleaned.columns
    assert "invalid_web_metrics_flag" in cleaned.columns
    # 行 1: EmailClicks(1)<=EmailOpens(2) → 0；行 3 visits=0 有 pages → flag
    assert int(cleaned.loc[cleaned["CustomerID"] == 3, "invalid_web_metrics_flag"].iloc[0]) == 1


def test_email_inconsistent_detection() -> None:
    df = pd.DataFrame(
        {
            "EmailOpens": [1, 5],
            "EmailClicks": [3, 2],
            "WebsiteVisits": [1, 0],
            "PagesPerVisit": [1.0, 2.0],
            "TimeOnSite": [1.0, 0.0],
        }
    )
    out = add_quality_flags(df)
    assert list(out["email_inconsistent"]) == [1, 0]
    assert list(out["invalid_web_metrics_flag"]) == [0, 1]


def test_save_clean_does_not_touch_raw(sample_csv: Path, tmp_path: Path) -> None:
    before = sample_csv.read_bytes()
    df = clean_dataframe(load_raw_csv(sample_csv))
    meta = save_clean(df, tmp_path / "processed")
    assert meta["rows"] == 3
    assert (tmp_path / "processed" / "clean.csv").is_file()
    assert sample_csv.read_bytes() == before


def test_stratified_split_sizes(sample_csv: Path) -> None:
    # 扩大样本以便分层
    base = clean_dataframe(load_raw_csv(sample_csv))
    df = pd.concat([base] * 40, ignore_index=True)
    # 重新编号避免唯一约束问题（split 不要求 ID 唯一）
    train, valid, test, meta = stratified_three_way_split(
        df, test_size=0.15, valid_size=0.15, seed=42
    )
    assert meta["n_train"] + meta["n_valid"] + meta["n_test"] == len(df)
    assert meta["n_test"] > 0 and meta["n_valid"] > 0 and meta["n_train"] > 0


def test_feature_config_excludes_leakage() -> None:
    cfg = load_feature_config()
    cols = cfg.feature_columns()
    assert_no_leakage(cols)
    assert "CustomerID" not in cols
    assert "Conversion" not in cols
    assert "ConversionRate" not in cols
    assert "AdvertisingPlatform" not in cols


def test_profile_has_positive_rate(sample_csv: Path) -> None:
    df = clean_dataframe(load_raw_csv(sample_csv))
    profile = profile_dataframe(df)
    assert profile["n_rows"] == 3
    assert 0.0 <= profile["positive_rate"] <= 1.0
    assert isinstance(profile["issues"], list)
