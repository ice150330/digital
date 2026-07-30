"""阶段9 W9c：增强分析 API 端点契约测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from digital_marketing.api.main import create_app
from digital_marketing.core.config import clear_settings_cache
from digital_marketing.core.paths import project_root, resolve_under_root
from digital_marketing.data.db import reset_engine

FULL_READY = all(
    (resolve_under_root("outputs/metrics") / f"{r}.json").is_file()
    for r in ("E2_lightgbm_default", "E8_lightgbm_calibrated")
) and (resolve_under_root("outputs/simulate") / "budget_curve_E2_lightgbm_default.json").is_file()

pytestmark = pytest.mark.skipif(not FULL_READY, reason="需先运行 scripts/06/07/08 全量产物")


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = project_root()
    monkeypatch.setenv("DIGITAL_ROOT", str(root))
    monkeypatch.setenv("DIGITAL_DATABASE_URL", f"sqlite:///{(tmp_path / 'a.db').as_posix()}")
    clear_settings_cache()
    reset_engine()
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()
    clear_settings_cache()


def test_curves_envelope(client: TestClient):
    r = client.get("/api/v1/models/curves")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    d = body["data"]
    assert d["run_id"]
    assert len(d["pr_curve"]["precision"]) == len(d["pr_curve"]["recall"])
    assert len(d["roc_curve"]["fpr"]) == len(d["roc_curve"]["tpr"])
    assert d["ci"]["n_boot"] == 1000


def test_calibration_envelope(client: TestClient):
    r = client.get("/api/v1/models/calibration", params={"run_id": "E8_lightgbm_calibrated"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["method"] in ("sigmoid", "isotonic")
    for side in ("before", "after"):
        assert {"brier", "log_loss", "ece", "bins"} <= set(d[side])


def test_calibration_missing_run_gives_404(client: TestClient):
    r = client.get("/api/v1/models/calibration", params={"run_id": "E3_lightgbm_balanced"})
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ARTIFACT_MISSING"


def test_lift_envelope(client: TestClient):
    r = client.get("/api/v1/models/lift")
    assert r.status_code == 200
    d = r.json()["data"]
    assert len(d["lift_deciles"]) == 10
    first = d["lift_deciles"][0]
    assert {"decile", "n", "positives", "capture_rate", "lift"} <= set(first)


def test_threshold_scan_envelope(client: TestClient):
    r = client.get("/api/v1/models/threshold-scan")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["cost_fp"] == 1.0 and d["cost_fn"] == 5.0
    assert d["rows"] and d["best_by_cost"]
    assert d["current_threshold"] is not None


def test_pdp_envelope_and_feature_filter(client: TestClient):
    r = client.get("/api/v1/explain/pdp")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["features"]
    feat = next(iter(d["features"]))
    r2 = client.get("/api/v1/explain/pdp", params={"feature": feat})
    assert r2.status_code == 200
    d2 = r2.json()["data"]
    assert d2["feature"] == feat
    assert len(d2["grid"]) == len(d2["pdp"])
    r3 = client.get("/api/v1/explain/pdp", params={"feature": "NoSuchFeature"})
    assert r3.json()["ok"] is False


def test_counterfactual_envelope(client: TestClient):
    r = client.post(
        "/api/v1/explain/counterfactual",
        json={"customer_id": 8000, "feature": "TimeOnSite", "target_proba": 0.95, "max_steps": 4},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["curve"]["feature"] == "TimeOnSite"
    assert len(d["curve"]["grid"]) == len(d["curve"]["proba"])
    cf = d["counterfactual"]
    assert "不构成因果" in cf["disclaimer"]
    assert cf["final_proba"] >= cf["base_proba"]


def test_simulate_budget_envelope(client: TestClient):
    r = client.post(
        "/api/v1/simulate/budget",
        json={"budget": 2000.0, "value_per_conversion": 10.0, "cost_per_contact": 4.0},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["n_population"] > 0
    assert max(c["k"] for c in d["curve"]) <= 500  # 2000/4
    assert "非因果" in d["disclaimer"] or "不构成" in d["disclaimer"]


def test_simulate_budget_validation(client: TestClient):
    r = client.post("/api/v1/simulate/budget", json={"value_per_conversion": -1})
    assert r.status_code == 422


def test_segments_projection_envelope(client: TestClient):
    if not (resolve_under_root("outputs/segments") / "compare.json").is_file():
        pytest.skip("需先运行 scripts/09_cluster_compare.py")
    r = client.get("/api/v1/segments/projection")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["points"] and {"x", "y", "cluster"} <= set(d["points"][0])


def test_openapi_lists_new_paths(client: TestClient):
    r = client.get("/openapi.json")
    paths = r.json()["paths"]
    for p in (
        "/api/v1/models/curves",
        "/api/v1/models/calibration",
        "/api/v1/models/lift",
        "/api/v1/models/threshold-scan",
        "/api/v1/explain/pdp",
        "/api/v1/explain/counterfactual",
        "/api/v1/simulate/budget",
        "/api/v1/segments/projection",
    ):
        assert p in paths, f"openapi 缺 {p}"
