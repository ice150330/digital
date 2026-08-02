"""PiAgent 上游模型列表发现。

约束：上游请求只在后端发起，API Key 不进入浏览器；当前按 OpenAI
compatible `GET /models` 响应解析，DeepSeek 默认地址作为空 base_url 兜底。
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from digital_marketing.agent.config import get_agent_config
from digital_marketing.agent.llm_client import get_llm_api_key


DEFAULT_MODEL_BASE_URL = "https://api.deepseek.com"


class UpstreamModelError(Exception):
    """上游模型列表获取失败。"""

    def __init__(self, message: str, *, code: str = "LLM_UNAVAILABLE", detail: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail or {}


def fetch_upstream_models(*, base_url: str | None = None, timeout_sec: int | None = None) -> dict[str, Any]:
    """读取上游模型列表，返回前端可直接消费的模型目录。"""
    cfg = get_agent_config()
    resolved_base_url = (base_url or cfg.llm.base_url or DEFAULT_MODEL_BASE_URL).strip().rstrip("/")
    if not resolved_base_url.startswith(("http://", "https://")):
        raise UpstreamModelError("Base URL 仅支持 http/https", code="VALIDATION_ERROR")

    timeout = int(timeout_sec or cfg.llm.timeout_sec or 60)
    api_key = get_llm_api_key()
    if not api_key:
        raise UpstreamModelError(
            "未配置 DEEPSEEK_API_KEY，无法从上游读取模型列表",
            code="LLM_UNAVAILABLE",
            detail={"base_url": resolved_base_url, "api_key_configured": False},
        )

    data = _request_models(resolved_base_url, api_key=api_key, timeout_sec=timeout)
    models = _parse_models(data)
    return {
        "base_url": resolved_base_url,
        "models": models,
        "n": len(models),
        "selected_model": cfg.pi.bridge_model,
        "source": {"kind": "openai-compatible", "endpoint": f"{resolved_base_url}/models"},
    }


def _request_models(base_url: str, *, api_key: str, timeout_sec: int) -> dict[str, Any]:
    req = Request(
        f"{base_url}/models",
        method="GET",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urlopen(req, timeout=timeout_sec) as resp:  # noqa: S310 - URL 来自已校验配置，仅服务端调用
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        raise UpstreamModelError(
            f"上游模型列表请求失败: HTTP {exc.code}",
            detail={"base_url": base_url, "status_code": exc.code},
        ) from exc
    except URLError as exc:
        raise UpstreamModelError(
            f"无法连接上游模型服务: {exc.reason}",
            detail={"base_url": base_url},
        ) from exc
    except TimeoutError as exc:
        raise UpstreamModelError(
            "上游模型列表请求超时",
            detail={"base_url": base_url, "timeout_sec": timeout_sec},
        ) from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UpstreamModelError("上游模型列表不是合法 JSON", detail={"base_url": base_url}) from exc
    if not isinstance(parsed, dict):
        raise UpstreamModelError("上游模型列表响应格式不正确", detail={"base_url": base_url})
    return parsed


def _parse_models(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = data.get("data") or data.get("models") or []
    if not isinstance(raw_items, list):
        raise UpstreamModelError("上游模型列表缺少 data 数组")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw_items:
        if isinstance(item, str):
            model_id = item.strip()
            owned_by = None
        elif isinstance(item, dict):
            model_id = str(item.get("id") or item.get("name") or "").strip()
            owned_by = item.get("owned_by") or item.get("owner")
        else:
            continue
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)
        items.append({"id": model_id, "label": model_id, "owned_by": owned_by})
    return sorted(items, key=lambda x: x["id"])
