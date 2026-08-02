"""OpenAPI 路径冒烟：关键端点已注册。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from digital_marketing.api.main import create_app
from digital_marketing.core.config import clear_settings_cache
from digital_marketing.data.db import reset_engine


REQUIRED_PATHS = {
    "/api/v1/health",
    "/api/v1/data/overview",
    "/api/v1/meta/features",
    "/api/v1/models/metrics",
    "/api/v1/models/predict",
    "/api/v1/models/predict/batch",
    "/api/v1/explain/global",
    "/api/v1/explain/customer",
    "/api/v1/segments",
    "/api/v1/segments/assign",
    "/api/v1/rules",
    "/api/v1/agent/chat",
    "/api/v1/agent/chat/stream",
    "/api/v1/agent/sessions",
    "/api/v1/agent/pi/config",
    "/api/v1/agent/pi/models",
    "/api/v1/agent/pi/status",
    "/api/v1/agent/runtime",
}


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("DIGITAL_ROOT", str(root))
    monkeypatch.setenv("DIGITAL_DATABASE_URL", f"sqlite:///{(tmp_path / 'o.db').as_posix()}")
    clear_settings_cache()
    reset_engine()
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()
    clear_settings_cache()


def test_openapi_contains_p0_p1_paths(client: TestClient):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = set(r.json().get("paths") or {})
    missing = REQUIRED_PATHS - paths
    assert not missing, f"OpenAPI 缺少路径: {missing}"


def test_cors_origins_include_frontend_port():
    from digital_marketing.core.config import get_settings

    clear_settings_cache()
    s = get_settings()
    joined = " ".join(s.cors_origins)
    assert "5600" in joined
    assert "5173" not in joined
