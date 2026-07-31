"""Agent 工具与 chat 契约测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from digital_marketing.agent.grounding import REQUIRED_SECTIONS
from digital_marketing.agent.pi_runtime import pi_executable_path, pi_status
from digital_marketing.agent.tools import list_tools, run_tool
from digital_marketing.api.main import create_app
from digital_marketing.core.config import clear_settings_cache
from digital_marketing.core.paths import project_root
from digital_marketing.data.db import reset_engine


def test_tool_registry_has_p0():
    names = set(list_tools())
    for t in (
        "get_dataset_profile",
        "get_data_quality_issues",
        "conversion_by_dimension",
        "get_model_metrics",
        "get_feature_schema",
        "predict_proba",
        "explain_global",
        "explain_customer",
    ):
        assert t in names


def test_pi_path_under_tools_pi_cli():
    path = pi_executable_path()
    root = project_root().resolve()
    assert "tools" in path.parts and "pi-cli" in path.parts
    path.resolve().relative_to((root / "tools" / "pi-cli").resolve())
    st = pi_status()
    assert st["valid_prefix"] is True


@pytest.fixture()
def agent_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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


def test_agent_chat_contract(agent_client: TestClient):
    r = agent_client.post(
        "/api/v1/agent/chat",
        json={"message": "请给出数据规模和模型 PR-AUC"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    data = body["data"]
    for k in REQUIRED_SECTIONS:
        assert k in data
    assert data["tool_trace"]
    assert data["session_id"]
    assert data["runtime"] in {"local", "template", "pi"}


def test_unknown_tool():
    out = run_tool("not_a_real_tool")
    assert out["ok"] is False


# ---------------------------------------------------------------------------
# 阶段9 W9c：新工具注册与接地
# ---------------------------------------------------------------------------


def test_tool_registry_has_stage9():
    names = set(list_tools())
    for t in (
        "compare_experiments",
        "get_calibration_summary",
        "get_lift_table",
        "simulate_budget",
        "counterfactual_explain",
    ):
        assert t in names


def test_compare_experiments_tool():
    out = run_tool("compare_experiments")
    assert out["ok"] is True
    r = out["result"]
    assert r["n_runs"] >= 3
    assert r["items"]
    row = r["items"][0]
    for k in ("run_id", "pr_auc", "cv_pr_auc_mean", "pr_auc_ci_low", "pr_auc_ci_high"):
        assert k in row


def test_get_calibration_summary_tool():
    out = run_tool("get_calibration_summary")
    assert out["ok"] is True
    r = out["result"]
    assert r["method"] in ("sigmoid", "isotonic")
    assert r["brier_after"] is not None


def test_get_lift_table_tool():
    out = run_tool("get_lift_table")
    assert out["ok"] is True
    assert len(out["result"]["lift_deciles"]) == 10


def test_simulate_budget_tool():
    out = run_tool("simulate_budget", budget=1000.0)
    assert out["ok"] is True
    r = out["result"]
    assert r["recommended_k"] >= 0
    assert r["disclaimer"]


def test_counterfactual_tool_requires_customer():
    out = run_tool("counterfactual_explain")
    assert out["ok"] is False


def test_grounding_facts_for_new_tools():
    from digital_marketing.agent.grounding import facts_from_tool

    out = run_tool("get_lift_table")
    facts = facts_from_tool("get_lift_table", out)
    assert any("lift" in f for f in facts)

    out2 = run_tool("compare_experiments")
    facts2 = facts_from_tool("compare_experiments", out2)
    assert any("run=" in f for f in facts2)

    out3 = run_tool("counterfactual_explain", customer_id=8000, target_proba=0.95)
    if out3["ok"]:
        facts3 = facts_from_tool("counterfactual_explain", out3)
        assert any("反事实" in f for f in facts3)


def test_plan_tools_routes_stage9_keywords():
    from digital_marketing.agent.local_runtime import plan_tools

    plans = [name for name, _ in plan_tools("做一下实验对比和消融分析")]
    assert "compare_experiments" in plans
    plans2 = [name for name, _ in plan_tools("预算 2000 怎么分配触达名单")]
    assert "simulate_budget" in plans2
    plans3 = [name for name, _ in plan_tools("客户 8000 的反事实怎么改能到 0.9")]
    assert "counterfactual_explain" in plans3
    plans4 = [name for name, _ in plan_tools("校准前后 brier 对比")]
    assert "get_calibration_summary" in plans4
    plans5 = [name for name, _ in plan_tools("给我 lift 十分位增益表")]
    assert "get_lift_table" in plans5


# ---------------------------------------------------------------------------
# Stage 4：render_chart 声明式图表工具（chart-spec v1.0）
# ---------------------------------------------------------------------------


def test_render_chart_spec_is_pure_json():
    import json

    out = run_tool("render_chart", chart_type="bar", dataset="conversion_by_channel")
    assert out["ok"] is True
    spec = out["result"]
    json.dumps(spec, ensure_ascii=False)  # 纯 JSON 可序列化（无函数/对象）
    for k in (
        "spec_version", "chart_type", "title", "categories",
        "series", "value_format", "axis", "caliber", "source",
    ):
        assert k in spec, k
    assert spec["spec_version"] == "1.0"
    assert spec["categories"]
    assert spec["series"][0]["values"]


def test_render_chart_all_datasets():
    for ds in (
        "conversion_by_channel", "conversion_by_type", "leaderboard_pr",
        "age_hist", "income_hist", "adspend_hist",
        "segment_sizes", "lift_deciles", "global_shap_top",
    ):
        out = run_tool("render_chart", dataset=ds)
        assert out["ok"] is True, f"{ds}: {out.get('error')}"
        assert out["result"]["categories"], ds


def test_render_chart_rejects_invalid():
    bad_ds = run_tool("render_chart", dataset="not_a_dataset")
    assert bad_ds["ok"] is False
    assert "dataset" in bad_ds["error"]
    bad_type = run_tool("render_chart", chart_type="radar", dataset="age_hist")
    assert bad_type["ok"] is False
    assert "chart_type" in bad_type["error"]


def test_render_chart_facts_state_existence_not_numbers():
    from digital_marketing.agent.grounding import facts_from_tool

    out = run_tool("render_chart", dataset="conversion_by_channel")
    facts = facts_from_tool("render_chart", out)
    assert any("图表" in f for f in facts)
    # facts 只述存在性：不含任何数字（数字在图里，避免叙述与图不一致）
    assert not any(ch.isdigit() for f in facts for ch in f)


def test_plan_routes_render_chart():
    from digital_marketing.agent.local_runtime import plan_tools

    plans = [name for name, _ in plan_tools("画各渠道转化率柱状图")]
    assert "render_chart" in plans
    # 数据集推断：分群 → pie/segment_sizes
    kwargs = dict(plan_tools("画分群规模占比饼图"))
    assert kwargs.get("render_chart", {}).get("dataset") == "segment_sizes"
    # 「对比图」变体 → leaderboard_pr
    kwargs2 = dict(plan_tools("画实验矩阵 PR-AUC 对比图"))
    assert kwargs2.get("render_chart", {}).get("dataset") == "leaderboard_pr"
