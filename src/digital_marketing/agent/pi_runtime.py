"""项目内 Pi runtime：仅允许 tools/pi-cli/ 下可执行文件与桥接脚本。

编排中枢定位：agent.yaml 默认 runtime=pi；未安装/仅为 stub 时明确降级 local
并在响应中标注原因（pi_fallback + open_questions，契约不变）。

Stage 5 真实编排（范式参考 VibeStart：createAgentSession 同进程 SDK +
customTools 代理 + ExtensionFactory 注入）：
- `tools/pi-cli/bridge/chat.mjs`：Node 桥接进程（stdin 请求 / stdout JSONL 事件）
- 桥接内 customTools 的 execute 经 HTTP loopback 回宿主 POST /agent/tool-run，
  由 Python REGISTRY 实际计算——**数字永由宿主产出，Pi 只编排与叙述**（§9.1）
- 任何失败（node 缺失/包未装/超时/事件异常）→ 降级 local 并标注原因
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from digital_marketing.agent import audit, grounding, skills
from digital_marketing.agent.local_runtime import EventSink, persist_turn, run_local_chat
from digital_marketing.core.paths import project_root, resolve_under_root


class PiPathError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class PiBridgeError(Exception):
    """桥接调用失败（触发降级 local，非致命）。"""


def _agent_cfg() -> dict[str, Any]:
    """读取 agent 配置（dict 形态）。Stage 1：统一经 agent/config.py 缓存加载。"""
    from digital_marketing.agent.config import get_agent_cfg_dict

    return get_agent_cfg_dict()


def pi_executable_path() -> Path:
    """解析并校验 Pi 可执行路径必须在 tools/pi-cli 下。"""
    cfg = _agent_cfg()
    rel = (cfg.get("pi") or {}).get("executable") or "tools/pi-cli/node_modules/.bin/pi"
    # 禁止 which/PATH 回退
    path = resolve_under_root(str(rel))
    root = project_root().resolve()
    pi_root = (root / "tools" / "pi-cli").resolve()
    try:
        path.resolve().relative_to(pi_root)
    except ValueError as e:
        raise PiPathError("PI_PATH_INVALID", f"Pi 路径必须位于 tools/pi-cli/ 下: {path}") from e
    return path


def _resolve_existing(path: Path) -> Path | None:
    candidates = [path]
    if os.name == "nt":
        candidates.extend([path.with_suffix(".cmd"), Path(str(path) + ".cmd")])
    return next((p for p in candidates if p.is_file()), None)


def is_stub_executable(path: Path) -> bool:
    """检测 setup_pi_cli 写入的占位 stub（文件头含 pi-stub 标记）。"""
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:2000].lower()
    except OSError:
        return False
    return "pi-stub" in head


def _bridge_script() -> Path:
    return project_root() / "tools" / "pi-cli" / "bridge" / "chat.mjs"


def _bridge_ready() -> tuple[bool, str]:
    """桥接三要素：脚本在、node 在、SDK 包已装。"""
    if not _bridge_script().is_file():
        return False, "bridge/chat.mjs 缺失"
    if shutil.which("node") is None:
        return False, "未找到 node（桥接需要 node ≥ 22）"
    pkg_dir = project_root() / "tools" / "pi-cli" / "node_modules" / "@earendil-works" / "pi-coding-agent"
    if not pkg_dir.is_dir():
        return False, "未安装 @earendil-works/pi-coding-agent（python scripts/setup_pi_cli.py）"
    return True, ""


def _sessions_count() -> int:
    d = audit.session_dir()
    if not d.is_dir():
        return 0
    return sum(1 for _ in d.glob("*.json"))


def pi_status() -> dict[str, Any]:
    cfg = _agent_cfg()
    default_runtime = str(cfg.get("runtime") or "local")
    skill_list = skills.list_skills(cfg)
    bridge_ok, bridge_note = _bridge_ready()
    base: dict[str, Any] = {
        "valid_prefix": True,
        "default_runtime": default_runtime,
        "skills": [s["name"] for s in skill_list],
        "skills_detail": skill_list,
        "sessions_count": _sessions_count(),
        "bridge_ready": bridge_ok,
        "bridge_note": bridge_note or None,
    }
    try:
        path = pi_executable_path()
    except PiPathError as e:
        return {
            **base,
            "installed": False,
            "executable": None,
            "valid_prefix": False,
            "is_stub": False,
            "code": e.code,
            "message": e.message,
            "hint": "运行 python scripts/setup_pi_cli.py（仅项目内，禁止全局 pi）",
            "fallback_reason": e.message,
        }
    existing = _resolve_existing(path)
    if existing is None:
        return {
            **base,
            "installed": False,
            "executable": str(path),
            "is_stub": False,
            "code": "PI_NOT_INSTALLED",
            "message": "未找到项目内 Pi 可执行文件",
            "hint": "运行 python scripts/setup_pi_cli.py",
            "fallback_reason": "未安装项目内 Pi，默认 runtime=pi 将降级 local/template",
        }
    stub = is_stub_executable(existing)
    return {
        **base,
        "installed": True,
        "executable": str(existing),
        "is_stub": stub,
        "code": "PI_STUB" if stub else None,
        "message": (
            "项目内 Pi 为占位 stub（setup_pi_cli 默认写入），对话将降级 local/template"
            if stub
            else None
        ),
        "hint": (
            "stub 仅用于路径校验与降级演示；安装真实 Pi 包可设 PI_NPM_PACKAGE 后重跑 setup"
            if stub
            else "项目内 Pi 可用"
        ),
        "fallback_reason": ("stub 占位，非真实 Pi 宿主" if stub else None),
    }


def run_pi_chat(
    message: str,
    *,
    session_id: str,
    request_id: str,
    on_event: EventSink | None = None,
) -> dict[str, Any]:
    """Pi 编排入口（service.chat 分发至此）。

    stub/未安装/桥接失败 → 降级 local 并显式标注（pi_fallback + open_questions）。
    """
    t0 = audit.now_ms()
    status = pi_status()
    installed_real = status.get("installed") and not status.get("is_stub")
    if not installed_real:
        reason = status.get("fallback_reason") or status.get("message") or "Pi 不可用"
        return _fallback_local(message, session_id=session_id, request_id=request_id,
                               status=status, reason=str(reason), t0=t0, on_event=on_event)

    bridge_ok, bridge_note = _bridge_ready()
    if not bridge_ok:
        return _fallback_local(message, session_id=session_id, request_id=request_id,
                               status=status, reason=f"桥接未就绪：{bridge_note}", t0=t0, on_event=on_event)

    try:
        events = _run_bridge(message, status)
    except (PiBridgeError, subprocess.TimeoutExpired, OSError) as e:
        return _fallback_local(message, session_id=session_id, request_id=request_id,
                               status=status, reason=f"Pi 桥接失败已降级: {e}", t0=t0, on_event=on_event)

    _forward_bridge_events(events, on_event)

    try:
        payload = _assemble_from_events(events, session_id=session_id)
    except PiBridgeError as e:
        return _fallback_local(message, session_id=session_id, request_id=request_id,
                               status=status, reason=f"Pi 事件解析失败已降级: {e}", t0=t0, on_event=on_event)

    payload["pi_status"] = status
    return persist_turn(
        payload, request_id=request_id, session_id=session_id, message=message,
        tool_trace=payload.get("tool_trace") or [], t0=t0, runtime="pi", on_event=on_event,
    )


def _fallback_local(
    message: str, *, session_id: str, request_id: str,
    status: dict[str, Any], reason: str, t0: float, on_event: EventSink | None = None,
) -> dict[str, Any]:
    """降级 local（保留历史契约：pi_fallback + open_questions 中文原因）。"""
    buffered_events: list[tuple[str, dict[str, Any]]] = []

    def buffer_event(event: str, data: dict[str, Any]) -> None:
        buffered_events.append((event, data))

    result = run_local_chat(
        message,
        session_id=session_id,
        runtime="local",
        request_id=request_id,
        on_event=buffer_event if on_event is not None else None,
    )
    hint = status.get("hint") or ""
    result.setdefault("open_questions", []).append(
        f"默认 runtime=pi，但{reason}，本轮已降级 {result.get('runtime')}。{hint}"
    )
    result["pi_status"] = status
    result["pi_fallback"] = True
    if on_event is not None:
        for event, data in buffered_events:
            if event not in {"done", "open_questions"}:
                on_event(event, data)
        on_event("open_questions", {"items": result.get("open_questions") or []})
        on_event(
            "done",
            {
                "session_id": session_id,
                "latency_ms": result.get("latency_ms") or round(audit.now_ms() - t0, 2),
                "runtime": result.get("runtime") or "template",
                "pi_fallback": True,
                "pi_status": status,
            },
        )
    return result


def _forward_bridge_events(events: list[dict[str, Any]], on_event: EventSink | None) -> None:
    """转发桥接中可安全展示的工具事件，契约段由宿主落盘后统一发送。"""
    if on_event is None:
        return
    for event in events:
        etype = event.get("type")
        if etype == "tool_start":
            on_event("tool_start", {"tool": event.get("tool"), "args": event.get("args") or {}})
        elif etype == "tool_end":
            payload = {
                "tool": event.get("tool"),
                "args": event.get("args") or {},
                "ok": bool(event.get("ok")),
                "result": event.get("result") if event.get("ok") else None,
                "error": event.get("error"),
                "duration_ms": event.get("duration_ms"),
            }
            on_event("tool_end", payload)
            if payload["tool"] == "render_chart" and payload["ok"] and isinstance(payload["result"], dict):
                on_event("chart", {"spec": payload["result"]})


def _run_bridge(message: str, status: dict[str, Any]) -> list[dict[str, Any]]:
    """spawn node bridge/chat.mjs：stdin 请求，stdout JSONL 事件流。"""
    from digital_marketing.core.config import get_settings

    cfg = _agent_cfg()
    timeout_sec = int((cfg.get("pi") or {}).get("timeout_sec") or 180)
    api_base = f"http://127.0.0.1:9800{get_settings().api_prefix}"
    request = json.dumps(
        {
            "message": message,
            "api_base": api_base,
            "cwd": str(project_root()),
        },
        ensure_ascii=False,
    )
    env = {
        **os.environ,
        "PI_SKIP_VERSION_CHECK": "1",
        "PI_TELEMETRY": "0",
    }
    proc = subprocess.run(
        ["node", str(_bridge_script())],
        input=request,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(project_root()),
        timeout=timeout_sec,
        env=env,
        shell=False,
    )
    events: list[dict[str, Any]] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not events:
        tail = (proc.stderr or "")[-400:]
        raise PiBridgeError(f"桥接无事件输出（exit={proc.returncode}）: {tail}")
    err = next((e for e in events if e.get("type") == "error"), None)
    if err is not None:
        raise PiBridgeError(str(err.get("message") or "桥接错误"))
    return events


def _assemble_from_events(events: list[dict[str, Any]], *, session_id: str) -> dict[str, Any]:
    """桥接 JSONL 事件 → 五段契约 payload（数字经 grounding 从宿主工具结果抽取）。"""
    tool_trace: list[dict[str, Any]] = []
    facts: list[str] = []
    # tool_start 的 args 按工具名排队，与 tool_end 顺序配对
    pending_args: dict[str, list[dict[str, Any]]] = {}
    reply = ""
    done = False

    for e in events:
        etype = e.get("type")
        if etype == "tool_start":
            pending_args.setdefault(str(e.get("tool")), []).append(e.get("args") or {})
        elif etype == "tool_end":
            name = str(e.get("tool"))
            args_list = pending_args.get(name) or []
            args = args_list.pop(0) if args_list else {}
            ok = bool(e.get("ok"))
            result = e.get("result")
            error = e.get("error")
            tool_trace.append(
                {"tool": name, "args": args, "ok": ok, "error": error, "result": result if ok else None}
            )
            facts.extend(grounding.facts_from_tool(name, {"ok": ok, "result": result, "error": error}))
        elif etype == "done":
            reply = str(e.get("reply") or "")
            done = True

    if not done:
        raise PiBridgeError("桥接事件流缺少 done 事件")
    if not tool_trace:
        raise PiBridgeError("Pi 未调用任何宿主工具（无可接地数字）")

    inferences = [
        "以上数字均来自宿主工具/产物（Pi 仅编排与叙述），非模型臆造。",
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
        "答辩演示路径：总览大屏 → 模型 PR-AUC/Dummy → 客户解释 → 本页展开 tool_trace。",
    ]
    open_q: list[str] = []
    if not any(t.get("ok") for t in tool_trace):
        open_q.append("工具全部失败，请检查是否已运行 run_all 生成产物。")

    return grounding.build_structured_reply(
        runtime="pi",
        session_id=session_id,
        tool_trace=tool_trace,
        facts=facts,
        inferences=inferences,
        recommendations=recommendations,
        open_questions=open_q,
        reply=reply or None,
    )


# 兼容别名（旧调用方与测试：from ...pi_runtime import try_pi_or_fallback）
try_pi_or_fallback = run_pi_chat
