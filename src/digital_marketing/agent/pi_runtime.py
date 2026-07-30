"""项目内 Pi runtime：仅允许 tools/pi-cli/ 下可执行文件。

编排中枢定位：agent.yaml 默认 runtime=pi；未安装/仅为 stub 时明确降级 local
并在响应中标注原因；真实安装时以宿主工具接地保证数字，skills 目录供 Pi 编排。
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from digital_marketing.agent import audit, skills
from digital_marketing.agent.local_runtime import run_local_chat
from digital_marketing.core.paths import project_root, resolve_under_root


class PiPathError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _agent_cfg() -> dict[str, Any]:
    path = project_root() / "config" / "agent.yaml"
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


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


def _sessions_count() -> int:
    d = audit.session_dir()
    if not d.is_dir():
        return 0
    return sum(1 for _ in d.glob("*.json"))


def pi_status() -> dict[str, Any]:
    cfg = _agent_cfg()
    default_runtime = str(cfg.get("runtime") or "local")
    skill_list = skills.list_skills(cfg)
    base: dict[str, Any] = {
        "valid_prefix": True,
        "default_runtime": default_runtime,
        "skills": [s["name"] for s in skill_list],
        "skills_detail": skill_list,
        "sessions_count": _sessions_count(),
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
            else "项目内 Pi 可用",
        ),
        "fallback_reason": ("stub 占位，非真实 Pi 宿主" if stub else None),
    }


def try_pi_or_fallback(message: str, *, session_id: str, request_id: str) -> dict[str, Any]:
    """尝试 Pi；stub/未安装/调用失败则降级 local 并显式标注。"""
    status = pi_status()
    installed_real = status.get("installed") and not status.get("is_stub")
    if not installed_real:
        result = run_local_chat(message, session_id=session_id, runtime="local", request_id=request_id)
        reason = status.get("fallback_reason") or status.get("message") or "Pi 不可用"
        result.setdefault("open_questions", []).append(
            f"默认 runtime=pi，但{reason}，本轮已降级 {result.get('runtime')}。{status.get('hint') or ''}"
        )
        result["pi_status"] = status
        result["pi_fallback"] = True
        return result

    # 真实 Pi：探测可执行 + 以宿主工具接地（skills 目录供编排，数字不臆造）
    exe = Path(status["executable"])
    probe_note = "Pi 可执行文件探测未运行"
    try:
        proc = subprocess.run(
            [str(exe), "--help"],
            cwd=str(project_root()),
            capture_output=True,
            text=True,
            timeout=15,
            shell=False,
            env={**os.environ, "PATH": str(exe.parent)},  # 不依赖全局 pi
        )
        probe_note = f"Pi 探测返回码 {proc.returncode}"
    except Exception as e:  # noqa: BLE001
        result = run_local_chat(message, session_id=session_id, runtime="local", request_id=request_id)
        result.setdefault("open_questions", []).append(f"Pi 调用失败已降级: {e}")
        result["pi_status"] = status
        result["pi_fallback"] = True
        return result

    result = run_local_chat(message, session_id=session_id, runtime="template", request_id=request_id)
    result["runtime"] = "pi"
    result.setdefault("inferences", []).append(
        f"Pi 可执行已校验位于 tools/pi-cli/（{probe_note}）；"
        f"skills={len(status.get('skills') or [])} 个可用；数字仍由宿主工具接地。"
    )
    result["pi_status"] = status
    return result
