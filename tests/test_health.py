"""健康检查 API 测试。"""

from __future__ import annotations


def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["error"] is None
    assert "request_id" in body
    data = body["data"]
    assert data["status"] == "ok"
    assert data["database_ok"] is True
    assert data["campaigns_count"] == 3
    assert resp.headers.get("X-Request-Id")


def test_health_envelope_shape(client):
    body = client.get("/api/v1/health").json()
    assert set(body.keys()) >= {"ok", "data", "error", "request_id"}
