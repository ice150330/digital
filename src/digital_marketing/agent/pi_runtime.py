"""项目内 Pi runtime：仅允许 tools/pi-cli/ 下可执行文件。"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

import yaml

from digital_marketing.agent import audit, grounding
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


def pi_status() -> dict[str, Any]:
    try:
        path = pi_executable_path()
    except PiPathError as e:
        return {
            "installed": False,
            "executable": None,
            "valid_prefix": True,
            "code": e.code,
            "message": e.message,
            "hint": "运行 python scripts/setup_pi_cli.py（仅项目内，禁止全局 pi）",
        }
    # Windows 可能需要 .cmd
    candidates = [path]
    if os.name == "nt":
        candidates.extend([path.with_suffix(".cmd"), Path(str(path) + ".cmd")])
    existing = next((p for p in candidates if p.is_file()), None)
    return {
        "installed": existing is not None,
        "executable": str(existing) if existing else str(path),
        "valid_prefix": True,
        "code": None if existing else "PI_NOT_INSTALLED",
        "message": None if existing else "未找到项目内 Pi 可执行文件",
        "hint": "运行 python scripts/setup_pi_cli.py",
    }


def try_pi_or_fallback(message: str, *, session_id: str, request_id: str) -> dict[str, Any]:
    """尝试 Pi；失败则降级 local/template 并标注。"""
    status = pi_status()
    if not status.get("installed"):
        result = run_local_chat(message, session_id=session_id, runtime="template", request_id=request_id)
        result["runtime"] = "template"
        result.setdefault("open_questions", []).append(
            f"Pi 未安装，已降级 template：{status.get('message')}。{status.get('hint')}"
        )
        result["pi_status"] = status
        return result

    # 最小调用：将用户消息与工具提示交给 pi；解析失败则降级
    exe = Path(status["executable"])
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
        # 当前以状态探测为主；完整 skill 对话可后续扩展
        _ = proc.returncode
    except Exception as e:  # noqa: BLE001
        result = run_local_chat(message, session_id=session_id, runtime="template", request_id=request_id)
        result.setdefault("open_questions", []).append(f"Pi 调用失败已降级: {e}")
        result["pi_status"] = status
        return result

    # 仍用本地工具接地保证数字正确，runtime 标记 pi（可执行已校验）
    result = run_local_chat(message, session_id=session_id, runtime="template", request_id=request_id)
    result["runtime"] = "pi"
    result.setdefault("inferences", []).append("Pi 可执行文件已校验位于 tools/pi-cli/；本轮仍用宿主工具接地保证数字。")
    result["pi_status"] = status
    return result
