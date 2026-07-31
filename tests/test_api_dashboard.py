"""Stage 3：大屏描述性聚合端点（/data/dashboard、/data/cross-matrix）。

基于 conftest.client 的 3 行样本库，期望值以手工 SQL 口径复核：
- clicked=3（三行 ctr>0）/ visited=2 / deep_visited=2（pages≥2）/ converted=2
- KPI：n=3、positive_rate=2/3、total_ad_spend=450、avg_ctr=0.15、
  avg_pages_per_visit=2.0、repurchase_rate=2/3（行2、行3 previous_purchases>0）
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from digital_marketing.core.config import get_settings
from digital_marketing.data.db import get_engine, init_db, reset_engine


def test_dashboard_envelope_and_funnel_counts(client: TestClient):
    r = client.get("/api/v1/data/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    d = body["data"]

    # 伪漏斗四阶段，横截面独立计数（与手工 SQL 一致）
    counts = {f["stage"]: f["count"] for f in d["funnel"]}
    assert counts == {"clicked": 3, "visited": 2, "deep_visited": 2, "converted": 2}
    for f in d["funnel"]:
        assert 0 <= f["rate_vs_total"] <= 1
        assert f["label"]

    # KPI 聚合
    k = d["kpis"]
    assert k["n_rows"] == 3
    assert abs(k["positive_rate"] - 2 / 3) < 1e-4
    assert abs(k["total_ad_spend"] - 450.0) < 1e-6
    assert abs(k["avg_ctr"] - 0.15) < 1e-6
    assert abs(k["avg_pages_per_visit"] - 2.0) < 1e-6
    assert abs(k["repurchase_rate"] - 2 / 3) < 1e-4

    # 直方图三列，箱含 lo/hi/count 且总数 = n
    assert set(d["histograms"].keys()) == {"age", "income", "ad_spend"}
    for col, bins in d["histograms"].items():
        assert bins, col
        assert sum(b["count"] for b in bins) == 3
        for b in bins:
            assert b["lo"] <= b["hi"]

    # 口径真相源：横截面 / 非 cohort / 时序不可做
    assert "横截面" in d["caliber"]
    assert "cohort" in d["caliber"]
    assert "时序" in d["caliber"]
    assert d["notes"]["time_series_impossible"] is True
    assert d["source"].startswith("sqlite.campaigns")


def test_cross_matrix_default_dims(client: TestClient):
    r = client.get("/api/v1/data/cross-matrix")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["row_dim"] == "campaign_channel"
    assert d["col_dim"] == "campaign_type"
    assert sum(c["n"] for c in d["cells"]) == 3
    assert sum(t["n"] for t in d["row_totals"]) == 3
    assert sum(t["n"] for t in d["col_totals"]) == 3
    for c in d["cells"]:
        assert 0 <= c["conversion_rate"] <= 1
    assert "横截面" in d["caliber"]


def test_cross_matrix_gender_dim(client: TestClient):
    r = client.get("/api/v1/data/cross-matrix", params={"row_dim": "gender", "col_dim": "campaign_channel"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["row_dim"] == "gender"
    assert sum(c["n"] for c in d["cells"]) == 3


def test_cross_matrix_rejects_invalid_dim(client: TestClient):
    r = client.get("/api/v1/data/cross-matrix", params={"row_dim": "income; DROP TABLE campaigns", "col_dim": "gender"})
    assert r.status_code == 422
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_cross_matrix_rejects_same_dim(client: TestClient):
    r = client.get("/api/v1/data/cross-matrix", params={"row_dim": "gender", "col_dim": "gender"})
    assert r.status_code == 422
    assert r.json()["ok"] is False


def test_dashboard_empty_table_is_artifact_missing(tmp_db_path, sample_csv, monkeypatch):
    """空表（建表未导入）→ ARTIFACT_MISSING 而非 500。"""
    settings = get_settings()
    init_db(settings)  # 仅建表，不导入
    reset_engine()
    init_db(get_settings())

    from digital_marketing.api.main import create_app

    app = create_app()
    with TestClient(app) as c:
        r = c.get("/api/v1/data/dashboard")
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ARTIFACT_MISSING"
    assert "import_campaigns" in body["error"]["message"]
