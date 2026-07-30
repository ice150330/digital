"""Local / template 运行时：关键词路由 + 可选 LLM（无 Key 则模板）。"""

from __future__ import annotations

import os
import re
import uuid
from typing import Any

from digital_marketing.agent import audit, grounding
from digital_marketing.agent.tools import run_tool


def _load_agent_cfg() -> dict[str, Any]:
    from pathlib import Path

    import yaml

    from digital_marketing.core.paths import project_root

    path = project_root() / "config" / "agent.yaml"
    if not path.is_file():
        return {"runtime": "local"}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_runtime(requested: str | None = None) -> str:
    cfg = _load_agent_cfg()
    rt = (requested or cfg.get("runtime") or "local").lower()
    if rt == "pi":
        return "pi"
    # 无 Key 时强制 template 语义（仍可走关键词工具）
    key = os.environ.get("DIGITAL_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key and rt == "local":
        return "template"
    return rt if rt in {"local", "template", "pi"} else "template"


def plan_tools(message: str) -> list[tuple[str, dict[str, Any]]]:
    """基于关键词规划工具调用（确定性，可演示）。"""
    msg = message.lower()
    plans: list[tuple[str, dict[str, Any]]] = []

    # 客户 ID
    m = re.search(r"(?:customer(?:id)?|客户)\s*[#:=]?\s*(\d{1,8})", message, re.I)
    if not m:
        m = re.search(r"\b(\d{4,5})\b", message)
    cid = int(m.group(1)) if m else None

    if any(k in msg for k in ("质量", "quality", "issue", "异常", "不一致")):
        plans.append(("get_data_quality_issues", {}))
    if any(k in msg for k in ("渠道", "channel", "转化率", "conversion")):
        plans.append(("conversion_by_dimension", {"dimension": "CampaignChannel"}))
    if any(k in msg for k in ("指标", "metrics", "pr-auc", "prauc", "auc", "模型", "dummy")):
        plans.append(("get_model_metrics", {}))
    if any(k in msg for k in ("特征", "schema", "入模")):
        plans.append(("get_feature_schema", {}))
    if any(k in msg for k in ("全局", "global shap", "全局解释", "重要特征")):
        plans.append(("explain_global", {}))
    if any(k in msg for k in ("预测", "proba", "概率", "解释客户", "shap", "局部")) and cid is not None:
        plans.append(("predict_proba", {"customer_id": cid}))
        plans.append(("explain_customer", {"customer_id": cid, "top_k": 8}))
    elif any(k in msg for k in ("预测", "proba", "客户")) and cid is not None:
        plans.append(("predict_proba", {"customer_id": cid}))
    if any(k in msg for k in ("分群", "segment", "cluster", "簇")):
        plans.append(("segment_summary", {}))
        if cid is not None:
            plans.append(("assign_cluster", {"customer_id": cid}))
    if any(k in msg for k in ("规则", "association", "lift", "关联")):
        plans.append(("top_association_rules", {"min_lift": 1.0, "limit": 10}))
    # 阶段9：实验对比 / 校准 / 升降 / 预算模拟 / 反事实
    if any(k in msg for k in ("实验对比", "对比实验", "compare", "消融", "ablation", "stacking", "集成", "所有模型", "全量")):
        plans.append(("compare_experiments", {}))
    if any(k in msg for k in ("校准", "calibrat", "brier", "ece")):
        plans.append(("get_calibration_summary", {}))
    if any(k in msg for k in ("升降", "增益", "gains", "十分位", "decile")):
        plans.append(("get_lift_table", {}))
    if any(k in msg for k in ("预算", "budget", "触达", "名单", "roi", "收益模拟", "模拟")):
        plans.append(("simulate_budget", {}))
    if any(k in msg for k in ("报告", "report", "生成分析", "论文素材", "汇总报告")):
        plans.append(("generate_analysis_report", {}))
    if any(k in msg for k in ("反事实", "counterfactual", "如果", "what-if", "whatif", "怎么改", "如何提升概率")) and cid is not None:
        plans.append(("counterfactual_explain", {"customer_id": cid, "target_proba": 0.9}))
    if any(k in msg for k in ("策略", "brief", "综合", "建议摘要")):
        plans.append(("strategy_brief", {}))
    if any(k in msg for k in ("画像", "概览", "样本", "overview", "数据规模", "多少行")):
        plans.append(("get_dataset_profile", {}))

    if not plans:
        # 默认安全只读：数据画像 + 模型指标
        plans = [
            ("get_dataset_profile", {}),
            ("get_model_metrics", {}),
        ]
    # 去重保序
    seen: set[str] = set()
    uniq: list[tuple[str, dict[str, Any]]] = []
    for name, kwargs in plans:
        key = name + str(sorted(kwargs.items()))
        if key in seen:
            continue
        seen.add(key)
        uniq.append((name, kwargs))
    return uniq[:6]


def run_local_chat(
    message: str,
    *,
    session_id: str | None = None,
    runtime: str | None = None,
    request_id: str = "unknown",
) -> dict[str, Any]:
    """执行一轮对话：规划工具 → 执行 → 契约化回复。"""
    t0 = audit.now_ms()
    sid = session_id or str(uuid.uuid4())
    rt = resolve_runtime(runtime)
    if rt == "pi":
        # 阶段 7 PiRuntime；此处若未装则降级
        from digital_marketing.agent.pi_runtime import try_pi_or_fallback

        return try_pi_or_fallback(message, session_id=sid, request_id=request_id)

    plans = plan_tools(message)
    tool_trace: list[dict[str, Any]] = []
    facts: list[str] = []
    for name, kwargs in plans:
        result = run_tool(name, **kwargs)
        tool_trace.append(
            {
                "tool": name,
                "args": kwargs,
                "ok": result.get("ok"),
                "error": result.get("error"),
                "result": result.get("result") if result.get("ok") else None,
            }
        )
        facts.extend(grounding.facts_from_tool(name, result))

    inferences = [
        "以上数字均来自工具/产物，非模型臆造。",
        "Accuracy 仅作对照；主指标为 PR-AUC。",
    ]
    if any(t.get("tool") == "top_association_rules" for t in tool_trace):
        inferences.append("关联规则为相关关系，不构成因果结论。")
    if any(t.get("tool") == "segment_summary" for t in tool_trace):
        inferences.append("分群训练不含 Conversion，簇转化率为事后统计。")
    if any(t.get("tool") == "simulate_budget" for t in tool_trace):
        inferences.append("预算模拟为期望值口径（概率×价值−成本），非因果 uplift。")
    if any(t.get("tool") == "counterfactual_explain" for t in tool_trace):
        inferences.append("反事实为模型行为（敏感性）分析，不构成因果建议。")

    recommendations = [
        "答辩演示路径：总览 → 模型 PR-AUC/Dummy → 客户解释 → 本页展开 tool_trace。",
    ]
    if rt == "template":
        recommendations.append("当前为 template/关键词模式（未配置 LLM Key），工具结果仍真实可用。")

    open_q = []
    if not any(t.get("ok") for t in tool_trace):
        open_q.append("工具全部失败，请检查是否已运行 run_all 生成产物。")

    payload = grounding.build_structured_reply(
        runtime=rt,
        session_id=sid,
        tool_trace=tool_trace,
        facts=facts,
        inferences=inferences,
        recommendations=recommendations,
        open_questions=open_q,
    )

    latency = audit.now_ms() - t0
    audit.append_audit(
        {
            "request_id": request_id,
            "session_id": sid,
            "runtime": rt,
            "user_message": message[:2000],
            "tool_calls": [{"tool": t["tool"], "ok": t["ok"]} for t in tool_trace],
            "reply_digest": (payload.get("reply") or "")[:500],
            "latency_ms": round(latency, 2),
            "error": None,
        }
    )
    prev = audit.load_session(sid) or {"session_id": sid, "messages": []}
    prev.setdefault("messages", []).append({"role": "user", "content": message})
    prev["messages"].append({"role": "assistant", "content": payload})
    prev["runtime"] = rt
    audit.save_session(sid, prev)
    payload["latency_ms"] = round(latency, 2)
    return payload
