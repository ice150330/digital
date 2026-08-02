"""Stage 1：agent 统一配置 + 装饰器工具注册 + 白名单校验测试。"""

from __future__ import annotations

import os

import pytest

import digital_marketing.agent.config as agent_config
from digital_marketing.agent.config import (
    AgentConfig,
    clear_agent_config_cache,
    get_agent_config,
    get_pi_agent_settings,
    set_runtime_persisted,
    update_pi_agent_settings,
)
from digital_marketing.agent.tools import REGISTRY, list_tools, plan_from_message, run_tool


@pytest.fixture(autouse=True)
def _config_cache_clean():
    clear_agent_config_cache()
    yield
    clear_agent_config_cache()


def test_repo_agent_yaml_defaults():
    """仓库内 agent.yaml：runtime=pi、Pi 路径在 tools/pi-cli 下、白名单非空。"""
    cfg = get_agent_config()
    assert isinstance(cfg, AgentConfig)
    assert cfg.runtime == "pi"
    assert cfg.pi.executable.startswith("tools/pi-cli/")
    assert cfg.pi.timeout_sec == 180
    assert cfg.pi.bridge_model == "deepseek/deepseek-chat"
    assert cfg.audit.log_dir == "outputs/agent_logs"
    assert len(cfg.tools_whitelist) >= 18


def test_config_is_cached():
    a = get_agent_config()
    b = get_agent_config()
    assert a is b
    clear_agent_config_cache()
    assert get_agent_config() is not a


def test_missing_yaml_falls_back_to_local(tmp_path, monkeypatch):
    """无 agent.yaml 时 runtime 兜底 local（与原 _load_agent_cfg 行为一致）。"""
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    clear_agent_config_cache()
    cfg = get_agent_config()
    assert cfg.runtime == "local"
    assert cfg.tools_whitelist == []


def test_set_runtime_persisted_roundtrip(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text("runtime: pi\n", encoding="utf-8")
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    clear_agent_config_cache()

    new_cfg = set_runtime_persisted("local")
    assert new_cfg.runtime == "local"
    # 缓存已失效：再取仍是写回后的值
    assert get_agent_config().runtime == "local"
    text = (tmp_path / "config" / "agent.yaml").read_text(encoding="utf-8")
    assert "runtime: local" in text


def test_pi_agent_settings_update_masks_secret_and_writes_yaml(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text(
        "runtime: pi\nllm:\n  base_url: ''\n  timeout_sec: 60\npi:\n  executable: tools/pi-cli/node_modules/.bin/pi\n  timeout_sec: 180\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    clear_agent_config_cache()

    settings = update_pi_agent_settings(
        {
            "runtime": "local",
            "llm": {"base_url": "https://api.deepseek.com/", "timeout_sec": 45},
            "pi": {
                "executable": "tools/pi-cli/node_modules/.bin/pi",
                "skills_dir": "src/digital_marketing/agent/skills",
                "session_dir": "outputs/agent_sessions",
                "timeout_sec": 150,
                "bridge_model": "deepseek/deepseek-chat",
            },
            "api_key": "sk-test-secret-value",
        }
    )

    text = (tmp_path / "config" / "agent.yaml").read_text(encoding="utf-8")
    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "runtime: local" in text
    assert "base_url: https://api.deepseek.com" in text
    assert "bridge_model: deepseek/deepseek-chat" in text
    assert "DEEPSEEK_API_KEY=sk-test-secret-value" in env_text
    assert settings["llm"]["api_key_configured"] is True
    assert settings["llm"]["api_key_preview"] == "sk-t…alue"
    assert "sk-test-secret-value" not in str(settings)
    assert get_pi_agent_settings()["runtime"] == "local"


def test_pi_agent_settings_clear_secret_keeps_other_env(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text("runtime: pi\n", encoding="utf-8")
    (tmp_path / ".env").write_text("FOO=bar\nDEEPSEEK_API_KEY=sk-old-secret\n", encoding="utf-8")
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-old-secret")
    clear_agent_config_cache()

    settings = update_pi_agent_settings({"clear_api_key": True})

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "FOO=bar" in env_text
    assert "DEEPSEEK_API_KEY" not in env_text
    assert settings["llm"]["api_key_configured"] is False
    assert "DEEPSEEK_API_KEY" not in os.environ


def test_pi_agent_settings_validation_rejects_unsafe_inputs(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text("runtime: pi\n", encoding="utf-8")
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    clear_agent_config_cache()

    bad_payloads = [
        {"runtime": "global"},
        {"llm": {"base_url": "ftp://api.example.com"}},
        {"llm": {"timeout_sec": 3}},
        {"pi": {"timeout_sec": 500}},
        {"pi": {"executable": "pi"}},
        {"pi": {"executable": "scripts/pi"}},
        {"pi": {"bridge_model": "deepseek-chat"}},
        {"pi": {"session_dir": "../outside"}},
        {"api_key": "sk-test\nBAD=1"},
    ]
    for payload in bad_payloads:
        with pytest.raises(ValueError):
            update_pi_agent_settings(payload)


def test_run_tool_whitelist_enforced(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent.yaml").write_text(
        "runtime: local\ntools:\n  whitelist:\n    - get_dataset_profile\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent_config, "project_root", lambda: tmp_path)
    clear_agent_config_cache()

    blocked = run_tool("simulate_budget")
    assert blocked["ok"] is False
    assert "白名单" in blocked["error"]

    allowed = run_tool("get_dataset_profile")
    # 白名单放行（工具自身成败取决于产物，此处只验未被白名单拦截）
    assert "白名单" not in str(allowed.get("error"))


def test_registry_complete():
    names = set(list_tools())
    assert len(REGISTRY) >= 18
    for t in (
        "get_dataset_profile",
        "get_data_quality_issues",
        "conversion_by_dimension",
        "get_model_metrics",
        "get_feature_schema",
        "predict_proba",
        "explain_global",
        "explain_customer",
        "segment_summary",
        "assign_cluster",
        "top_association_rules",
        "strategy_brief",
        "compare_experiments",
        "get_calibration_summary",
        "get_lift_table",
        "simulate_budget",
        "counterfactual_explain",
        "generate_analysis_report",
    ):
        assert t in names
    # 每个工具必须可经关键词或定制规划路由（否则 chat 永远触达不到）
    for meta in REGISTRY.values():
        assert meta.keywords or meta.plan is not None, f"{meta.name} 无路由方式"
        assert meta.facts is not None, f"{meta.name} 缺 facts 抽取器"


def test_plan_from_message_keeps_legacy_behaviors():
    # customer_id 抽取 + cid 依赖工具
    plans = dict(plan_from_message("解释客户 8001 的 shap"))
    assert plans.get("predict_proba") == {"customer_id": 8001}
    assert plans.get("explain_customer") == {"customer_id": 8001, "top_k": 8}

    # 无 cid 时不规划 cid 依赖工具（原行为）
    plans2 = [n for n, _ in plan_from_message("预测一下转化率")]
    assert "predict_proba" not in plans2

    # 默认兜底
    fallback = plan_from_message("zzz 无意义输入 qqq")
    assert fallback == [("get_dataset_profile", {}), ("get_model_metrics", {})]

    # 去重保序 + 上限 6
    many = plan_from_message(
        "质量 渠道 指标 特征 全局 分群 规则 实验对比 校准 增益 预算 报告 策略 画像"
    )
    assert len(many) <= 6
    keys = [n + str(sorted(k.items())) for n, k in many]
    assert len(keys) == len(set(keys))


def test_unknown_tool_and_fallback_facts():
    from digital_marketing.agent.grounding import facts_from_tool

    out = run_tool("not_a_real_tool")
    assert out["ok"] is False
    # 未知工具的 facts 走失败分支
    assert facts_from_tool("not_a_real_tool", out) == ["工具 not_a_real_tool 失败: 未知工具: not_a_real_tool"]
