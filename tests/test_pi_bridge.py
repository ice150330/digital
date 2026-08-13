"""Stage 5：Pi 桥接（manifest/tool-run 端点 + 事件装配 + 降级链）。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import digital_marketing.agent.pi_runtime as pr
from digital_marketing.agent.pi_runtime import PiBridgeError, _assemble_from_events, pi_status
from digital_marketing.api.main import create_app
from digital_marketing.core.config import clear_settings_cache
from digital_marketing.core.paths import project_root
from digital_marketing.data.db import reset_engine


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


# ---------------------------------------------------------------------------
# 端点：manifest / tool-run
# ---------------------------------------------------------------------------


def test_tools_manifest_endpoint(client: TestClient):
    r = client.get("/api/v1/agent/tools/manifest")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["n"] >= 19
    names = {t["name"] for t in d["tools"]}
    assert {"get_dataset_profile", "render_chart", "simulate_budget"} <= names
    for t in d["tools"]:
        assert t["description"], t["name"]
        assert "parameters" in t


def test_tool_run_endpoint_loopback(client: TestClient):
    r = client.post("/api/v1/agent/tool-run", json={"name": "get_dataset_profile", "args": {}})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["ok"] is True
    assert d["tool"] == "get_dataset_profile"
    assert d["result"]["n_rows"] == 8000

    bad = client.post("/api/v1/agent/tool-run", json={"name": "not_a_tool", "args": {}})
    bd = bad.json()["data"]
    assert bd["ok"] is False
    assert bd["error"]


def test_tool_run_validates_args_on_host(client: TestClient):
    """宿主侧真实校验：非法 dataset → ok=False（桥接仅代理，不自行校验）。"""
    r = client.post(
        "/api/v1/agent/tool-run",
        json={"name": "render_chart", "args": {"dataset": "evil; drop table"}},
    )
    d = r.json()["data"]
    assert d["ok"] is False
    assert "dataset" in d["error"]


# ---------------------------------------------------------------------------
# 事件装配：JSONL → 五段契约
# ---------------------------------------------------------------------------

FAKE_EVENTS = [
    {"type": "ready", "model": "deepseek-chat", "n_tools": 19},
    {"type": "tool_start", "tool": "get_dataset_profile", "args": {}},
    {"type": "tool_end", "tool": "get_dataset_profile", "ok": True,
     "result": {"n_rows": 8000, "positive_rate": 0.8765}, "error": None},
    {"type": "tool_start", "tool": "get_model_metrics", "args": {}},
    {"type": "tool_end", "tool": "get_model_metrics", "ok": True,
     "result": {"items": [{"run_id": "E2", "pr_auc": 0.948, "roc_auc": 0.91, "accuracy": 0.88}]},
     "error": None},
    {"type": "done", "reply": "【观察事实】样本量 8000，正类占比 87.65%。", "model": "deepseek-chat",
     "n_tool_calls": 2},
]


def test_assemble_events_five_sections():
    payload = _assemble_from_events(FAKE_EVENTS, session_id="t-bridge")
    assert payload["runtime"] == "pi"
    assert payload["reply"].startswith("【观察事实】")
    assert [t["tool"] for t in payload["tool_trace"]] == ["get_dataset_profile", "get_model_metrics"]
    assert payload["tool_trace"][0]["args"] == {}
    # facts 经 grounding 从宿主工具结果抽取（数字可追溯）
    assert any("8000" in f for f in payload["observed_facts"])
    assert any("PR-AUC" in f for f in payload["observed_facts"])
    assert any("PR-AUC" in i for i in payload["inferences"])


def test_assemble_events_requires_tools():
    """Pi 未调用任何工具 → 拒绝装配（无可接地数字），触发降级。"""
    events = [{"type": "done", "reply": "你好", "model": "x", "n_tool_calls": 0}]
    with pytest.raises(PiBridgeError):
        _assemble_from_events(events, session_id="t")


def test_assemble_events_requires_done():
    with pytest.raises(PiBridgeError):
        _assemble_from_events(FAKE_EVENTS[:-1], session_id="t")


def test_assemble_events_requires_real_reply():
    events = [
        {"type": "tool_start", "tool": "get_dataset_profile", "args": {}},
        {"type": "tool_end", "tool": "get_dataset_profile", "ok": True, "result": {"n_rows": 8000}},
        {"type": "done", "reply": "", "model": "deepseek-chat", "n_tool_calls": 1},
    ]
    with pytest.raises(PiBridgeError):
        _assemble_from_events(events, session_id="t-empty-reply")


# ---------------------------------------------------------------------------
# 降级链与 pi_status
# ---------------------------------------------------------------------------


def test_pi_status_has_bridge_fields():
    st = pi_status()
    assert "bridge_ready" in st
    assert "bridge_note" in st
    # 未安装 SDK 时 bridge_ready=False 且 note 说明原因
    if not st["bridge_ready"]:
        assert st["bridge_note"]


def test_pi_status_api_exposes_bridge_fields(client: TestClient):
    """DTO 层守门：bridge_ready 必须经 API 透出（防 pydantic 丢额外字段）。"""
    r = client.get("/api/v1/agent/pi/status")
    assert r.status_code == 200
    d = r.json()["data"]
    assert "bridge_ready" in d
    assert "bridge_note" in d
    assert isinstance(d["bridge_ready"], bool)


def test_run_bridge_injects_agent_config_env(monkeypatch):
    captured: dict[str, object] = {}

    class FakeProc:
        returncode = 0
        stdout = '{"type":"ready","model":"deepseek/deepseek-chat"}\n{"type":"done","reply":"ok"}\n'
        stderr = ""

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeProc()

    monkeypatch.setattr(
        pr,
        "_agent_cfg",
        lambda: {
            "pi": {"timeout_sec": 123, "bridge_model": "deepseek/deepseek-chat"},
            "llm": {"base_url": "https://api.deepseek.com", "timeout_sec": 45},
        },
    )
    monkeypatch.setattr("digital_marketing.agent.llm_client.get_llm_api_key", lambda: "sk-unit-test")
    monkeypatch.setattr(pr.subprocess, "run", fake_run)

    events = pr._run_bridge("数据规模", {})

    env = captured["kwargs"]["env"]
    assert captured["kwargs"]["timeout"] == 123
    assert env["PI_BRIDGE_MODEL"] == "deepseek/deepseek-chat"
    assert env["DEEPSEEK_API_KEY"] == "sk-unit-test"
    assert env["DEEPSEEK_BASE_URL"] == "https://api.deepseek.com"
    assert env["OPENAI_BASE_URL"] == "https://api.deepseek.com"
    assert [e["type"] for e in events] == ["ready", "done"]


def test_run_pi_chat_fallback_when_bridge_not_ready(monkeypatch, tmp_path):
    """桥接未就绪 → 降级 local，pi_fallback=True + open_questions 中文原因（契约不变）。"""
    monkeypatch.setattr(pr, "_bridge_ready", lambda: (False, "测试：桥接未就绪"))
    monkeypatch.setattr(
        pr, "pi_status",
        lambda: {"installed": True, "is_stub": False, "hint": "", "fallback_reason": None,
                 "default_runtime": "pi", "skills": [], "skills_detail": [],
                 "sessions_count": 0, "valid_prefix": True, "executable": "x",
                 "bridge_ready": False, "bridge_note": "测试"},
    )
    monkeypatch.setattr(
        "digital_marketing.agent.llm_client.chat_completion",
        lambda messages, **kwargs: {"reply": "真实 LLM mock：桥接未就绪降级。", "model": "deepseek-chat"},
    )
    result = pr.run_pi_chat("数据规模多少", session_id="t-fallback", request_id="req-fb")
    assert result["pi_fallback"] is True
    assert result["runtime"] in {"local", "template"}
    assert any("桥接未就绪" in q for q in result["open_questions"])
    assert result["tool_trace"]  # 降级后宿主工具仍执行


def test_run_pi_chat_assembles_when_bridge_ok(monkeypatch):
    """mock 桥接事件流 → run_pi_chat 产出 runtime=pi 的五段契约 + 审计落盘。"""
    monkeypatch.setattr(pr, "_bridge_ready", lambda: (True, ""))
    monkeypatch.setattr(
        pr, "pi_status",
        lambda: {"installed": True, "is_stub": False, "hint": "", "fallback_reason": None,
                 "default_runtime": "pi", "skills": [], "skills_detail": [],
                 "sessions_count": 0, "valid_prefix": True, "executable": "x",
                 "bridge_ready": True, "bridge_note": None},
    )
    monkeypatch.setattr(pr, "_run_bridge", lambda message, status, **kwargs: FAKE_EVENTS)

    result = pr.run_pi_chat("数据规模和模型指标", session_id="t-bridge-ok", request_id="req-ok")
    assert result["runtime"] == "pi"
    assert "pi_fallback" not in result or result["pi_fallback"] is False
    assert len(result["tool_trace"]) == 2
    assert result["reply"].startswith("【观察事实】")
    assert result["latency_ms"] is not None
    assert result["pi_status"]["installed"] is True


def test_run_pi_chat_fallback_on_bridge_error(monkeypatch):
    """桥接抛错 → 降级 local 并标注原因。"""
    monkeypatch.setattr(pr, "_bridge_ready", lambda: (True, ""))
    monkeypatch.setattr(
        pr, "pi_status",
        lambda: {"installed": True, "is_stub": False, "hint": "", "fallback_reason": None,
                 "default_runtime": "pi", "skills": [], "skills_detail": [],
                 "sessions_count": 0, "valid_prefix": True, "executable": "x",
                 "bridge_ready": True, "bridge_note": None},
    )

    def boom(message, status, **kwargs):
        raise PiBridgeError("测试：桥接崩溃")

    monkeypatch.setattr(pr, "_run_bridge", boom)
    monkeypatch.setattr(
        "digital_marketing.agent.llm_client.chat_completion",
        lambda messages, **kwargs: {"reply": "真实 LLM mock：桥接失败降级。", "model": "deepseek-chat"},
    )
    result = pr.run_pi_chat("数据规模", session_id="t-bridge-err", request_id="req-err")
    assert result["pi_fallback"] is True
    assert any("桥接崩溃" in q for q in result["open_questions"])
