"""Agent 上游 LLM 回复客户端测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import digital_marketing.agent.config as agent_config
import digital_marketing.agent.llm_client as llm_client
from digital_marketing.agent.config import clear_agent_config_cache
from digital_marketing.agent.llm_client import LlmUnavailableError, chat_completion, generate_grounded_reply


@pytest.fixture(autouse=True)
def _clean_config_cache():
    clear_agent_config_cache()
    yield
    clear_agent_config_cache()


def test_chat_completion_requires_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text("runtime: local\n", encoding="utf-8")
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    monkeypatch.delenv("DIGITAL_LLM_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(LlmUnavailableError) as exc:
        chat_completion([{"role": "user", "content": "hi"}])
    assert exc.value.code == "LLM_UNAVAILABLE"
    assert "DEEPSEEK_API_KEY" in exc.value.message


def test_chat_completion_posts_openai_compatible_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text(
        "runtime: local\nllm:\n  base_url: https://api.deepseek.com\n  timeout_sec: 22\npi:\n  bridge_model: deepseek/deepseek-chat\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-unit-test")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps(
                {"model": "deepseek-chat", "choices": [{"message": {"content": "真实 AI 回复"}}]}
            ).encode("utf-8")

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["auth"] = req.headers.get("Authorization")
        captured["timeout"] = timeout
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(llm_client, "urlopen", fake_urlopen)

    out = chat_completion([{"role": "user", "content": "数据规模"}])

    assert out["reply"] == "真实 AI 回复"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["auth"] == "Bearer sk-unit-test"
    assert captured["timeout"] == 22
    assert captured["body"]["model"] == "deepseek-chat"


def test_generate_grounded_reply_includes_tool_context(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return {"reply": "基于工具事实回答", "model": "deepseek-chat"}

    monkeypatch.setattr(llm_client, "chat_completion", fake_chat)

    out = generate_grounded_reply(
        user_message="画渠道转化率",
        facts=["渠道 Email 转化率最高"],
        inferences=["以上数字均来自工具/产物，非模型臆造。"],
        recommendations=["查看图表"],
        open_questions=[],
        tool_trace=[{"tool": "render_chart", "args": {"dataset": "conversion_by_channel"}, "ok": True}],
        history=[{"role": "user", "content": "上一轮"}],
    )

    assert out["reply"] == "基于工具事实回答"
    prompt = captured["messages"][-1]["content"]
    assert "渠道 Email 转化率最高" in prompt
    assert "render_chart" in prompt
