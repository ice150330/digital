"""训练与指标落盘测试（小样本）。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from digital_marketing.data.clean import clean_dataframe
from digital_marketing.data.load import load_raw_csv
from digital_marketing.data.split import stratified_three_way_split
from digital_marketing.features.build import fit_feature_bundle
from digital_marketing.features.schema import assert_no_leakage, load_feature_config
from digital_marketing.models.classify import run_experiment, write_leaderboard
from digital_marketing.models.metrics import evaluate_at_threshold, search_threshold_f1


def _expanded_frame(sample_csv: Path) -> pd.DataFrame:
    base = clean_dataframe(load_raw_csv(sample_csv))
    # 复制并轻微扰动数值，保证可分层与可训练
    frames = []
    rng = np.random.default_rng(42)
    for i in range(50):
        chunk = base.copy()
        chunk["CustomerID"] = chunk["CustomerID"] + i * 10
        chunk["Income"] = chunk["Income"] + rng.normal(0, 100, size=len(chunk))
        chunk["AdSpend"] = chunk["AdSpend"] + rng.normal(0, 10, size=len(chunk))
        frames.append(chunk)
    return pd.concat(frames, ignore_index=True)


def test_search_threshold_and_eval() -> None:
    y = np.array([0, 0, 1, 1, 1, 0, 1, 0])
    p = np.array([0.1, 0.2, 0.8, 0.7, 0.9, 0.3, 0.6, 0.4])
    thr, f1 = search_threshold_f1(y, p)
    assert 0.05 <= thr <= 0.95
    m = evaluate_at_threshold(y, p, thr)
    assert "pr_auc" in m and "confusion" in m
    assert f1 >= 0


def test_train_e0_writes_metrics(sample_csv: Path, tmp_path: Path) -> None:
    df = _expanded_frame(sample_csv)
    train, valid, test, _ = stratified_three_way_split(df, seed=42)
    cfg = load_feature_config()
    cols = cfg.feature_columns()
    assert_no_leakage(cols)
    assert "CustomerID" not in cols
    assert "ConversionRate" not in cols

    bundle = fit_feature_bundle(train, cfg)
    X_train = bundle.transform(train)
    X_valid = bundle.transform(valid)
    X_test = bundle.transform(test)
    y_train = train[cfg.target].astype(int).to_numpy()
    y_valid = valid[cfg.target].astype(int).to_numpy()
    y_test = test[cfg.target].astype(int).to_numpy()

    models_dir = tmp_path / "models"
    metrics_dir = tmp_path / "metrics"
    row = run_experiment(
        exp={"id": "E0", "name": "dummy_majority", "kind": "dummy"},
        X_train=X_train,
        y_train=y_train,
        X_valid=X_valid,
        y_valid=y_valid,
        X_test=X_test,
        y_test=y_test,
        seed=42,
        models_dir=models_dir,
        metrics_dir=metrics_dir,
        feature_schema={"feature_columns_raw": cols},
    )
    assert row["run_id"] == "E0_dummy_majority"
    assert "pr_auc" in row
    assert (metrics_dir / "E0_dummy_majority.json").is_file()
    assert (models_dir / "E0_dummy_majority" / "model.joblib").is_file()

    board = write_leaderboard([row], metrics_dir)
    assert board.is_file()


def test_logistic_experiment_runs(sample_csv: Path, tmp_path: Path) -> None:
    df = _expanded_frame(sample_csv)
    train, valid, test, _ = stratified_three_way_split(df, seed=0)
    cfg = load_feature_config()
    bundle = fit_feature_bundle(train, cfg)
    row = run_experiment(
        exp={
            "id": "E1",
            "name": "logistic_balanced",
            "kind": "logistic",
            "class_weight": "balanced",
        },
        X_train=bundle.transform(train),
        y_train=train[cfg.target].astype(int).to_numpy(),
        X_valid=bundle.transform(valid),
        y_valid=valid[cfg.target].astype(int).to_numpy(),
        X_test=bundle.transform(test),
        y_test=test[cfg.target].astype(int).to_numpy(),
        seed=0,
        models_dir=tmp_path / "models",
        metrics_dir=tmp_path / "metrics",
    )
    assert row["pr_auc"] is not None
    assert 0.0 <= row["accuracy"] <= 1.0
