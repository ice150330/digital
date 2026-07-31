"""Agent 工具注册中心（Stage 1：装饰器一处定义，收敛六处手工联动）。

一个工具只需在 catalog.py 用 @tool(...) 声明：实现函数 + 关键词/规划回调 +
facts 抽取器 + plan_order + stage；REGISTRY、plan_from_message 关键词路由、
grounding 事实分派、agent.yaml whitelist 校验自动生效。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

ToolFn = Callable[..., dict[str, Any]]
PlanFn = Callable[[str, "int | None"], "dict[str, Any] | None"]
FactsFn = Callable[[dict[str, Any]], list[str]]


@dataclass(frozen=True)
class ToolMeta:
    """工具元数据：装饰器一处定义的全部契约。"""

    name: str
    fn: ToolFn
    keywords: tuple[str, ...] = ()
    # 关键词命中时附带的固定参数（如 dimension=CampaignChannel）
    base_kwargs: dict[str, Any] = field(default_factory=dict)
    # 定制规划（需要 customer_id 等上下文时）；返回 None = 本轮不规划该工具
    plan: PlanFn | None = None
    # grounding 事实抽取器；None = 走兜底键名分支
    facts: FactsFn | None = None
    # 规划顺序（保持历史 plan_tools 的 append 顺序，影响 [:6] 截断与 trace 次序）
    plan_order: int = 100
    stage: str = ""


REGISTRY: dict[str, ToolMeta] = {}


def tool(
    name: str,
    *,
    keywords: tuple[str, ...] | list[str] = (),
    base_kwargs: dict[str, Any] | None = None,
    plan: PlanFn | None = None,
    facts: FactsFn | None = None,
    plan_order: int = 100,
    stage: str = "",
) -> Callable[[ToolFn], ToolFn]:
    """装饰器：把工具函数登记进 REGISTRY（幂等，重名覆盖以便测试热替换）。"""

    def deco(fn: ToolFn) -> ToolFn:
        REGISTRY[name] = ToolMeta(
            name=name,
            fn=fn,
            keywords=tuple(keywords),
            base_kwargs=dict(base_kwargs or {}),
            plan=plan,
            facts=facts,
            plan_order=plan_order,
            stage=stage,
        )
        return fn

    return deco


def list_tools() -> list[str]:
    return sorted(REGISTRY.keys())


def run_tool(name: str, **kwargs: Any) -> dict[str, Any]:
    """执行工具并统一包封 {ok, tool, result|error}；whitelist 非空时校验交集。"""
    if name not in REGISTRY:
        return {"ok": False, "error": f"未知工具: {name}", "tool": name}
    # 延迟导入避免与 config 的加载时序耦合；白名单为空 = 放行全部已注册工具
    from digital_marketing.agent.config import get_agent_config

    whitelist = get_agent_config().tools_whitelist
    if whitelist and name not in whitelist:
        return {"ok": False, "error": f"工具不在白名单: {name}", "tool": name}
    try:
        result = REGISTRY[name].fn(**kwargs)
        return {"ok": True, "tool": name, "result": result}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "tool": name, "error": str(e)}


def _extract_customer_id(message: str) -> int | None:
    """从消息抽取客户 ID（搬迁自原 plan_tools，行为不变）。"""
    m = re.search(r"(?:customer(?:id)?|客户)\s*[#:=]?\s*(\d{1,8})", message, re.I)
    if not m:
        m = re.search(r"\b(\d{4,5})\b", message)
    return int(m.group(1)) if m else None


def plan_from_message(message: str) -> list[tuple[str, dict[str, Any]]]:
    """基于注册元数据的确定性关键词规划（替代原 local_runtime.plan_tools）。

    保留三行为：customer_id 正则抽取、去重保序、[:6] 截断、
    无命中时默认 (get_dataset_profile, get_model_metrics) 安全兜底。
    """
    msg = message.lower()
    cid = _extract_customer_id(message)
    plans: list[tuple[str, dict[str, Any]]] = []
    for meta in sorted(REGISTRY.values(), key=lambda m: (m.plan_order, m.name)):
        if meta.plan is not None:
            kwargs = meta.plan(message, cid)
            if kwargs is not None:
                plans.append((meta.name, dict(kwargs)))
        elif meta.keywords and any(k in msg for k in meta.keywords):
            plans.append((meta.name, dict(meta.base_kwargs)))

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


# 历史名别名（测试与旧调用方可继续 from ... import plan_tools）
plan_tools = plan_from_message

# 触发 catalog 装饰器注册（必须置于 REGISTRY/装饰器定义之后）
from digital_marketing.agent.tools import catalog  # noqa: E402,F401
