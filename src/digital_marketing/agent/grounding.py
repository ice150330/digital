"""Agent 输出契约：五段字段 + tool_trace，禁止无工具编造数字。"""

from __future__ import annotations

from typing import Any


REQUIRED_SECTIONS = (
    "observed_facts",
    "inferences",
    "recommendations",
    "open_questions",
    "tool_trace",
)


def empty_result(*, runtime: str, session_id: str, message: str = "") -> dict[str, Any]:
    return {
        "runtime": runtime,
        "session_id": session_id,
        "observed_facts": [],
        "inferences": [],
        "recommendations": [],
        "open_questions": [message] if message else [],
        "tool_trace": [],
        "reply": message or "暂无工具结果。",
    }


def build_structured_reply(
    *,
    runtime: str,
    session_id: str,
    tool_trace: list[dict[str, Any]],
    facts: list[str],
    inferences: list[str],
    recommendations: list[str],
    open_questions: list[str] | None = None,
    reply: str | None = None,
) -> dict[str, Any]:
    """组装契约化响应。"""
    body = {
        "runtime": runtime,
        "session_id": session_id,
        "observed_facts": facts,
        "inferences": inferences,
        "recommendations": recommendations,
        "open_questions": open_questions or [],
        "tool_trace": tool_trace,
        "reply": reply
        or _compose_reply(facts, inferences, recommendations, open_questions or []),
    }
    for k in REQUIRED_SECTIONS:
        if k not in body:
            body[k] = [] if k != "tool_trace" else []
    return body


def _compose_reply(
    facts: list[str],
    inferences: list[str],
    recommendations: list[str],
    open_questions: list[str],
) -> str:
    parts: list[str] = []
    if facts:
        parts.append("【观察事实】\n" + "\n".join(f"- {x}" for x in facts))
    if inferences:
        parts.append("【推断】\n" + "\n".join(f"- {x}" for x in inferences))
    if recommendations:
        parts.append("【建议】\n" + "\n".join(f"- {x}" for x in recommendations))
    if open_questions:
        parts.append("【待确认】\n" + "\n".join(f"- {x}" for x in open_questions))
    if not parts:
        return "已执行工具，但未提炼出可展示事实。请查看 tool_trace。"
    return "\n\n".join(parts)


def facts_from_tool(tool: str, payload: dict[str, Any]) -> list[str]:
    """从工具结果抽取可引用事实字符串（仅基于结果，不编造）。

    Stage 1：分派壳。具体抽取器随 @tool 装饰器注册在
    agent/tools/facts.py（ToolMeta.facts）；本函数保持原入口签名，
    not-ok 分支与兜底键名分支行为不变。
    """
    if not payload.get("ok"):
        return [f"工具 {tool} 失败: {payload.get('error')}"]
    from digital_marketing.agent.tools import REGISTRY

    meta = REGISTRY.get(tool)
    if meta is not None and meta.facts is not None:
        return meta.facts(payload)
    r = payload.get("result") or {}
    return [f"工具 {tool} 已返回结果键: {list(r.keys())[:8]}"]
