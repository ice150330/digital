"""PiAgent 上游模型列表。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import digital_marketing.agent.config as agent_config
import digital_marketing.agent.model_catalog as model_catalog
from digital_marketing.agent.config import clear_agent_config_cache
from digital_marketing.agent.model_catalog import UpstreamModelError, fetch_upstream_models
from digital_marketing.api.main import create_app
from digital_marketing.core.config import clear_settings_cache
from digital_marketing.core.paths import project_root
from digital_marketing.data.db import reset_engine


@pytest.fixture(autouse=True)
def _clean_config_cache():
    clear_agent_config_cache()
    yield
    clear_agent_config_cache()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = project_root()
    monkeypatch.setenv("DIGITAL_ROOT", str(root))
    monkeypatch.setenv("DIGITAL_DATABASE_URL", f"sqlite:///{(tmp_path / 'models.db').as_posix()}")
    clear_settings_cache()
    reset_engine()
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()
    clear_settings_cache()


def test_fetch_upstream_models_requires_local_key(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text(
        "runtime: pi\nllm:\n  base_url: https://api.deepseek.com\npi:\n  bridge_model: deepseek/deepseek-chat\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    monkeypatch.delenv("DIGITAL_LLM_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(UpstreamModelError) as exc:
        fetch_upstream_models()
    assert exc.value.code == "LLM_UNAVAILABLE"
    assert "DEEPSEEK_API_KEY" in exc.value.message


def test_fetch_upstream_models_parses_openai_compatible_response(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text(
        "runtime: pi\nllm:\n  base_url: https://api.deepseek.com\n  timeout_sec: 30\npi:\n  bridge_model: deepseek/deepseek-chat\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-unit-test")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps(
                {
                    "data": [
                        {"id": "deepseek-chat", "owned_by": "deepseek"},
                        {"id": "deepseek-reasoner", "owned_by": "deepseek"},
                        {"id": "deepseek-chat", "owned_by": "deepseek"},
                    ]
                }
            ).encode("utf-8")

    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["auth"] = req.headers.get("Authorization")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(model_catalog, "urlopen", fake_urlopen)

    data = fetch_upstream_models()

    assert captured["url"] == "https://api.deepseek.com/models"
    assert captured["auth"] == "Bearer sk-unit-test"
    assert captured["timeout"] == 30
    assert data["n"] == 2
    assert [m["id"] for m in data["models"]] == ["deepseek-chat", "deepseek-reasoner"]
    assert data["selected_model"] == "deepseek/deepseek-chat"


def test_pi_models_api_returns_catalog(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "digital_marketing.api.routes_agent.fetch_upstream_models",
        lambda: {
            "base_url": "https://api.deepseek.com",
            "models": [{"id": "deepseek-chat", "label": "deepseek-chat", "owned_by": "deepseek"}],
            "n": 1,
            "selected_model": "deepseek/deepseek-chat",
            "source": {"kind": "openai-compatible", "endpoint": "https://api.deepseek.com/models"},
        },
    )

    r = client.get("/api/v1/agent/pi/models")

    assert r.status_code == 200
    d = r.json()["data"]
    assert d["n"] == 1
    assert d["models"][0]["id"] == "deepseek-chat"


def test_pi_models_api_reports_upstream_error(client: TestClient, monkeypatch):
    def fail():
        raise UpstreamModelError("未配置 DEEPSEEK_API_KEY", detail={"api_key_configured": False})

    monkeypatch.setattr("digital_marketing.api.routes_agent.fetch_upstream_models", fail)

    r = client.get("/api/v1/agent/pi/models")

    assert r.status_code == 502
    body = r.json()
    assert body["error"]["code"] == "LLM_UNAVAILABLE"
    assert "DEEPSEEK_API_KEY" in body["error"]["message"]
