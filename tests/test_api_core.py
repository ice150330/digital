"""P0 业务 API：overview / metrics / predict / explain。"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.dummy import DummyClassifier

from digital_marketing.api.main import create_app
from digital_marketing.core.config import clear_settings_cache
from digital_marketing.data.db import reset_engine


class _SelectColsTransformer:
    """可 pickle 的迷你 transformer。"""

    def __init__(self, cols: list[str]):
        self.cols = cols

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        return frame[self.cols].to_numpy(dtype=float)


@pytest.fixture()
def artifact_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sample_csv: Path):
    """在临时 outputs 下准备最小产物并挂 API。"""
    root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("DIGITAL_ROOT", str(root))
    db_path = tmp_path / "t.db"
    monkeypatch.setenv("DIGITAL_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    clear_settings_cache()
    reset_engine()

    out = tmp_path / "outputs"
    processed = out / "processed"
    models = out / "models" / "E0_dummy"
    metrics = out / "metrics"
    explain = out / "explain"
    for d in (processed, models, metrics, explain):
        d.mkdir(parents=True)

    from digital_marketing.data.clean import clean_dataframe
    from digital_marketing.data.load import load_raw_csv

    df = clean_dataframe(load_raw_csv(sample_csv))
    df.to_csv(processed / "clean.csv", index=False)
    (processed / "clean_meta.json").write_text(
        json.dumps(
            {
                "rows": len(df),
                "positive_rate": float(df["Conversion"].mean()),
                "email_inconsistent_count": int(df["email_inconsistent"].sum()),
                "invalid_web_metrics_count": int(df["invalid_web_metrics_flag"].sum()),
            }
        ),
        encoding="utf-8",
    )
    profile = {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "positive_rate": float(df["Conversion"].mean()),
        "issues": [{"code": "email_inconsistent", "count": 0, "message": "demo"}],
        "channel_stats": [{"channel": "Email", "n": 1, "conversion_rate": 1.0}],
    }
    (processed / "quality_profile.json").write_text(json.dumps(profile), encoding="utf-8")
    (processed / "splits.json").write_text(
        json.dumps({"n_train": 2, "n_valid": 1, "n_test": 0}), encoding="utf-8"
    )

    cols = ["Age", "Income"]
    X = df[cols].to_numpy(dtype=float)
    y = df["Conversion"].astype(int).to_numpy()
    model = DummyClassifier(strategy="prior").fit(X, y)
    transformer = _SelectColsTransformer(cols)
    joblib.dump(model, models / "model.joblib")
    schema = {
        "feature_columns_raw": cols,
        "feature_names_out": cols,
        "target": "Conversion",
        "drop_features": ["ConversionRate"],
        "never_features": ["CustomerID", "Conversion"],
        "transformer_path": str(processed / "feature_transformer.joblib"),
    }
    joblib.dump(transformer, processed / "feature_transformer.joblib")
    (processed / "feature_schema.json").write_text(json.dumps(schema), encoding="utf-8")
    (models / "meta.json").write_text(
        json.dumps(
            {
                "run_id": "E0_dummy",
                "model_name": "dummy",
                "threshold": 0.5,
                "feature_schema": schema,
            }
        ),
        encoding="utf-8",
    )
    (metrics / "E0_dummy.json").write_text(
        json.dumps(
            {
                "run_id": "E0_dummy",
                "exp_id": "E0",
                "model_name": "dummy",
                "pr_auc": 0.5,
                "roc_auc": 0.5,
                "f1": 0.5,
                "accuracy": 0.5,
                "threshold": 0.5,
            }
        ),
        encoding="utf-8",
    )
    (metrics / "leaderboard.json").write_text(
        json.dumps(
            [
                {
                    "run_id": "E0_dummy",
                    "exp_id": "E0",
                    "model_name": "dummy",
                    "pr_auc": 0.5,
                    "roc_auc": 0.5,
                    "f1": 0.5,
                    "accuracy": 0.5,
                    "threshold": 0.5,
                }
            ]
        ),
        encoding="utf-8",
    )
    (explain / "global_E0_dummy.json").write_text(
        json.dumps(
            {
                "run_id": "E0_dummy",
                "method": "test",
                "n_samples": 3,
                "top_features": [{"name": "Age", "mean_abs_shap": 0.1}],
            }
        ),
        encoding="utf-8",
    )

    import digital_marketing.services.artifacts as art

    monkeypatch.setattr(art, "processed_dir", lambda: processed)
    monkeypatch.setattr(art, "metrics_dir", lambda: metrics)
    monkeypatch.setattr(art, "models_dir", lambda: out / "models")
    monkeypatch.setattr(art, "explain_dir", lambda: explain)

    app = create_app()
    with TestClient(app) as c:
        yield c

    reset_engine()
    clear_settings_cache()


def test_overview_ok(artifact_client: TestClient) -> None:
    r = artifact_client.get("/api/v1/data/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["n_rows"] == 3
    assert "request_id" in body


def test_metrics_list(artifact_client: TestClient) -> None:
    r = artifact_client.get("/api/v1/models/metrics")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert items[0]["run_id"] == "E0_dummy"
    assert "pr_auc" in items[0]


def test_predict_by_customer(artifact_client: TestClient) -> None:
    r = artifact_client.post("/api/v1/models/predict", json={"customer_id": 1})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "proba" in data and "threshold" in data and "run_id" in data
    assert data["run_id"] == "E0_dummy"


def test_explain_global(artifact_client: TestClient) -> None:
    r = artifact_client.get("/api/v1/explain/global")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["method"] == "test"
    assert data["top_features"]


def test_metrics_missing_run(artifact_client: TestClient) -> None:
    r = artifact_client.get("/api/v1/models/metrics/not_exist")
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ARTIFACT_MISSING"
