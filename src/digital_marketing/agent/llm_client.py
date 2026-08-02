"""上游 LLM 客户端：用于工具接地后的真实会话回复。"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from digital_marketing.agent.config import get_agent_config, get_deepseek_api_key


DEFAULT_CHAT_BASE_URL = "https://api.deepseek.com"


class LlmUnavailableError(Exception):
    """上游 LLM 不可用；不得回退为假装 AI 的硬编码回复。"""

    def __init__(self, message: str, *, detail: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = "LLM_UNAVAILABLE"
        self.message = message
        self.detail = detail or {}


def get_llm_api_key() -> str:
    """读取项目本地 LLM Key；只供服务端请求上游使用。"""
    return (
        os.environ.get("DIGITAL_LLM_API_KEY", "").strip()
        or get_deepseek_api_key().strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )


def selected_chat_model() -> str:
    """返回 OpenAI-compatible chat/completions 可识别的模型名。"""
    cfg = get_agent_config()
    raw = (cfg.pi.bridge_model or cfg.llm.model or "deepseek-chat").strip()
    # UI 里保存 provider/model；上游 chat/completions 通常只接受 model 部分。
    return raw.split("/", 1)[1] if "/" in raw else raw


def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    base_url: str | None = None,
    timeout_sec: int | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """调用 OpenAI-compatible chat/completions，返回 reply/model/usage。"""
    cfg = get_agent_config()
    resolved_base = (base_url or cfg.llm.base_url or DEFAULT_CHAT_BASE_URL).strip().rstrip("/")
    if not resolved_base.startswith(("http://", "https://")):
        raise LlmUnavailableError("Base URL 仅支持 http/https", detail={"base_url": resolved_base})

    api_key = get_llm_api_key()
    if not api_key:
        raise LlmUnavailableError(
            "未配置 DEEPSEEK_API_KEY，无法生成真实 AI 回复",
            detail={"base_url": resolved_base, "api_key_configured": False},
        )

    payload = json.dumps(
        {
            "model": model or selected_chat_model(),
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = Request(
        f"{resolved_base}/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    timeout = int(timeout_sec or cfg.llm.timeout_sec or 60)
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - URL 来自配置校验，仅后端调用
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        raise LlmUnavailableError(
            f"上游 AI 回复请求失败: HTTP {exc.code}",
            detail={"base_url": resolved_base, "status_code": exc.code},
        ) from exc
    except URLError as exc:
        raise LlmUnavailableError(f"无法连接上游 AI 服务: {exc.reason}", detail={"base_url": resolved_base}) from exc
    except TimeoutError as exc:
        raise LlmUnavailableError("上游 AI 回复请求超时", detail={"base_url": resolved_base, "timeout_sec": timeout}) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmUnavailableError("上游 AI 回复不是合法 JSON", detail={"base_url": resolved_base}) from exc
    reply = _extract_reply(data)
    if not reply:
        raise LlmUnavailableError("上游 AI 回复为空", detail={"base_url": resolved_base})
    return {"reply": reply, "model": data.get("model") or model or selected_chat_model(), "usage": data.get("usage")}


def generate_grounded_reply(
    *,
    user_message: str,
    facts: list[str],
    inferences: list[str],
    recommendations: list[str],
    open_questions: list[str],
    tool_trace: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """把工具事实交给上游模型组织自然语言回复。"""
    messages = _build_messages(
        user_message=user_message,
        facts=facts,
        inferences=inferences,
        recommendations=recommendations,
        open_questions=open_questions,
        tool_trace=tool_trace,
        history=history or [],
    )
    return chat_completion(messages)


def _build_messages(
    *,
    user_message: str,
    facts: list[str],
    inferences: list[str],
    recommendations: list[str],
    open_questions: list[str],
    tool_trace: list[dict[str, Any]],
    history: list[dict[str, str]],
) -> list[dict[str, str]]:
    tool_summary = [
        {
            "tool": item.get("tool"),
            "args": item.get("args") or {},
            "ok": bool(item.get("ok")),
            "error": item.get("error"),
        }
        for item in tool_trace[:8]
    ]
    context = {
        "user_message": user_message,
        "observed_facts": facts,
        "inferences": inferences,
        "recommendations": recommendations,
        "open_questions": open_questions,
        "tool_trace": tool_summary,
    }
    system = (
        "你是数字营销转化分析系统里的真实 AI 分析助手。"
        "所有数字、指标、SHAP、转化率、预算收益只能引用用户本轮工具结果中的 observed_facts 和 tool_trace；"
        "不要编造数字，不要声称因果效果。用中文回答，先直接回答用户问题，再补充必要口径。"
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    messages.extend(_clean_history(history))
    messages.append(
        {
            "role": "user",
            "content": "请基于以下宿主工具结果回答本轮问题：\n"
            + json.dumps(context, ensure_ascii=False, default=str),
        }
    )
    return messages


def _clean_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for item in history[-8:]:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        cleaned.append({"role": role, "content": content[:1600]})
    return cleaned


def _extract_reply(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") or {}
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"].strip()
        text = first.get("text")
        if isinstance(text, str):
            return text.strip()
    if isinstance(data.get("reply"), str):
        return data["reply"].strip()
    return ""
