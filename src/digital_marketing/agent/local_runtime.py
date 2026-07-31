"""Local / template 运行时：关键词路由 + 工具执行 + 契约化回复。

Stage 1：配置统一经 agent/config.py；关键词规划迁至 tools.plan_from_message
（装饰器元数据驱动）；runtime=pi 的分发上提至 service.chat，本模块不再内埋
Pi 分支（pi_runtime 降级时仍会回调 run_local_chat(runtime="local"|"template")）。
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from digital_marketing.agent import audit, grounding
from digital_marketing.agent.tools import plan_from_message, run_tool

# 历史名别名（旧调用方与测试：from ...local_runtime import plan_tools）
plan_tools = plan_from_message


def resolve_runtime(requested: str | None = None) -> str:
    from digital_marketing.agent.config import get_agent_config

    cfg = get_agent_config()
    rt = (requested or cfg.runtime or "local").lower()
    if rt == "pi":
        return "pi"
    # 无 Key 时强制 template 语义（仍可走关键词工具）
    key = os.environ.get("DIGITAL_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key and rt == "local":
        return "template"
    return rt if rt in {"local", "template", "pi"} else "template"


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
        # 分发上提至 service.chat；pi_runtime 降级链只会传 local/template
        raise RuntimeError("runtime=pi 的分发应经 agent.service.chat / pi_runtime.run_pi_chat")

    plans = plan_from_message(message)
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
    return persist_turn(
        payload, request_id=request_id, session_id=sid, message=message,
        tool_trace=tool_trace, t0=t0, runtime=rt,
    )


def persist_turn(
    payload: dict[str, Any],
    *,
    request_id: str,
    session_id: str,
    message: str,
    tool_trace: list[dict[str, Any]],
    t0: float,
    runtime: str,
) -> dict[str, Any]:
    """审计落盘 + 会话续写 + latency 回填（local 与 pi 两条路径共用）。"""
    latency = audit.now_ms() - t0
    audit.append_audit(
        {
            "request_id": request_id,
            "session_id": session_id,
            "runtime": runtime,
            "user_message": message[:2000],
            "tool_calls": [{"tool": t["tool"], "ok": t["ok"]} for t in tool_trace],
            "reply_digest": (payload.get("reply") or "")[:500],
            "latency_ms": round(latency, 2),
            "error": None,
        }
    )
    prev = audit.load_session(session_id) or {"session_id": session_id, "messages": []}
    prev.setdefault("messages", []).append({"role": "user", "content": message})
    prev["messages"].append({"role": "assistant", "content": payload})
    prev["runtime"] = runtime
    audit.save_session(session_id, prev)
    payload["latency_ms"] = round(latency, 2)
    return payload
