"""阶段9 W9d：Pi 编排中枢 —— 默认 runtime、stub 降级、skills、报告、审计。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from digital_marketing.agent.pi_runtime import pi_status, try_pi_or_fallback
from digital_marketing.agent.skills import list_skills
from digital_marketing.api.main import create_app
from digital_marketing.core.config import clear_settings_cache
from digital_marketing.core.paths import project_root, resolve_under_root
from digital_marketing.data.db import reset_engine


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = project_root()
    monkeypatch.setenv("DIGITAL_ROOT", str(root))
    monkeypatch.setenv("DIGITAL_DATABASE_URL", f"sqlite:///{(tmp_path / 'a.db').as_posix()}")
    monkeypatch.setattr(
        "digital_marketing.agent.llm_client.chat_completion",
        lambda messages, **kwargs: {"reply": "真实 LLM mock：runtime 测试回复。", "model": "deepseek-chat"},
    )
    clear_settings_cache()
    reset_engine()
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()
    clear_settings_cache()


def test_default_runtime_is_pi_in_config():
    import yaml

    cfg = yaml.safe_load((project_root() / "config" / "agent.yaml").read_text(encoding="utf-8"))
    assert cfg.get("runtime") == "pi"


def test_pi_status_enriched_fields():
    st = pi_status()
    for k in ("is_stub", "default_runtime", "skills", "sessions_count", "fallback_reason"):
        assert k in st
    assert st["default_runtime"] == "pi"
    assert st["valid_prefix"] is True
    # 兼容两种环境：stub（setup 占位）与真实安装（Stage 5 之后）
    if st["installed"]:
        if st["is_stub"]:
            assert st["code"] == "PI_STUB"
            assert st["fallback_reason"]
        else:
            assert st["code"] is None
            assert st["fallback_reason"] is None
    assert len(st["skills"]) == 7


def test_skills_frontmatter_parsed():
    skills = list_skills()
    names = {s["name"] for s in skills}
    assert {
        "channel-conversion-compare",
        "customer-shap-narrative",
        "segment-strategy-brief",
        "threshold-advisor",
        "budget-planner",
        "experiment-comparator",
        "report-writer",
    } <= names
    assert all(s["description"] for s in skills)


def test_stub_chat_falls_back_with_annotation(monkeypatch):
    st = pi_status()
    if not (st["installed"] and st["is_stub"]):
        pytest.skip("仅 stub 环境下验证降级标注")
    monkeypatch.setattr(
        "digital_marketing.agent.llm_client.chat_completion",
        lambda messages, **kwargs: {"reply": "真实 LLM mock：stub 降级回复。", "model": "deepseek-chat"},
    )
    result = try_pi_or_fallback("数据规模多少", session_id="t-w9d", request_id="req-w9d")
    assert result.get("pi_fallback") is True
    assert result["runtime"] in {"local", "template"}
    assert any("降级" in q for q in result.get("open_questions", []))
    # 数字仍来自工具（profile 默认工具应被调用）
    assert result.get("tool_trace")


def test_generate_report_tool_writes_markdown():
    from digital_marketing.agent.tools import run_tool

    out = run_tool("generate_analysis_report", title="测试报告W9D")
    assert out["ok"] is True
    r = out["result"]
    path = Path(r["report_path"])
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "测试报告W9D" in text
    assert "样本量 n_rows=8000" in text  # 数字来自工具
    assert "口径与限制" in text
    assert r["n_sections_ok"] >= 5
    assert all("tool" in t and "ok" in t for t in r["tool_trace"])
    path.unlink()  # 清理测试产物


def test_audit_recent_api(client: TestClient):
    # 先发一轮 chat 产生审计
    client.post("/api/v1/agent/chat", json={"message": "数据规模", "runtime": "local"}).json()
    r = client.get("/api/v1/agent/audit/recent", params={"limit": 5})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["n"] >= 1
    row = d["items"][0]
    for k in ("ts", "request_id", "runtime", "user_message", "tool_calls"):
        assert k in row


def test_pi_config_api_returns_settings_and_status(client: TestClient):
    r = client.get("/api/v1/agent/pi/config")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["settings"]["runtime"] == "pi"
    assert d["settings"]["pi"]["bridge_model"] == "deepseek/deepseek-chat"
    assert "api_key_configured" in d["settings"]["llm"]
    assert "api_key" not in d["settings"]["llm"]
    assert d["status"]["default_runtime"] == "pi"


def test_pi_config_api_rejects_invalid_pi_path(client: TestClient):
    r = client.put("/api/v1/agent/pi/config", json={"pi": {"executable": "pi"}})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "tools/pi-cli" in body["error"]["message"]


def test_report_api(client: TestClient):
    r = client.post("/api/v1/agent/report", json={"title": "API报告测试", "sections": ["数据画像与质量", "实验矩阵对比"]})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["n_sections"] == 2
    path = Path(d["report_path"])
    assert path.is_file()
    path.unlink()


def test_audit_dirs_from_yaml():
    from digital_marketing.agent import audit

    assert "agent_logs" in str(audit.log_dir())
    assert "agent_sessions" in str(audit.session_dir())
