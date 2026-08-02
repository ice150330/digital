"""Agent 统一配置：config/agent.yaml 单一加载点（缓存 + pydantic 校验）。

Stage 1 收敛：local_runtime / pi_runtime / audit / routes_agent 不再各自
yaml.safe_load，一律经 get_agent_config()；写回 runtime 经 set_runtime_persisted()
并自动失效缓存。缓存范式复刻 core/config.py::get_settings。
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, Field

from digital_marketing.core.paths import project_root


ALLOWED_RUNTIMES = {"pi", "local", "template"}
DEFAULT_BRIDGE_MODEL = "deepseek/deepseek-chat"
DEEPSEEK_KEY = "DEEPSEEK_API_KEY"
LLM_TIMEOUT_RANGE = (5, 180)
PI_TIMEOUT_RANGE = (30, 300)


class LlmConfig(BaseModel):
    """LLM 调用配置（Key 仅环境变量，不入 yaml）。"""

    base_url: str = ""
    model: str = "deepseek-chat"
    timeout_sec: int = 60


class PiConfig(BaseModel):
    """项目内 Pi CLI 配置（路径硬约束见 pi_runtime.pi_executable_path）。"""

    executable: str = "tools/pi-cli/node_modules/.bin/pi"
    skills_dir: str = "src/digital_marketing/agent/skills"
    session_dir: str = "outputs/agent_sessions"
    timeout_sec: int = 180
    bridge_model: str = DEFAULT_BRIDGE_MODEL


class AuditConfig(BaseModel):
    """审计 jsonl 与会话落盘目录。"""

    log_dir: str = "outputs/agent_logs"
    session_dir: str = "outputs/agent_sessions"


class AgentConfig(BaseModel):
    """config/agent.yaml 的校验快照。"""

    # 文件缺失时的兜底与原 local_runtime 行为一致（"local"）；
    # 仓库内 agent.yaml 显式声明 runtime: pi
    runtime: str = "local"
    llm: LlmConfig = Field(default_factory=LlmConfig)
    pi: PiConfig = Field(default_factory=PiConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    # 空列表 = 放行全部已注册工具；非空时 run_tool 校验交集
    tools_whitelist: list[str] = Field(default_factory=list)


def _agent_yaml_path():
    return project_root() / "config" / "agent.yaml"


def _dotenv_path() -> Path:
    return project_root() / ".env"


def _load_raw() -> dict[str, Any]:
    path = _agent_yaml_path()
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_raw(cfg: dict[str, Any]) -> None:
    path = _agent_yaml_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


@lru_cache(maxsize=1)
def get_agent_config() -> AgentConfig:
    """加载并缓存 AgentConfig。"""
    raw = _load_raw()
    llm = raw.get("llm") or {}
    pi = raw.get("pi") or {}
    audit = raw.get("audit") or {}
    tools = raw.get("tools") or {}
    return AgentConfig(
        runtime=str(raw.get("runtime") or "local"),
        llm=LlmConfig(
            base_url=str(llm.get("base_url") or ""),
            model=str(llm.get("model") or "deepseek-chat"),
            timeout_sec=int(llm.get("timeout_sec") or 60),
        ),
        pi=PiConfig(
            executable=str(pi.get("executable") or "tools/pi-cli/node_modules/.bin/pi"),
            skills_dir=str(pi.get("skills_dir") or "src/digital_marketing/agent/skills"),
            session_dir=str(pi.get("session_dir") or "outputs/agent_sessions"),
            timeout_sec=int(pi.get("timeout_sec") or 180),
            bridge_model=str(pi.get("bridge_model") or DEFAULT_BRIDGE_MODEL),
        ),
        audit=AuditConfig(
            log_dir=str(audit.get("log_dir") or "outputs/agent_logs"),
            session_dir=str(audit.get("session_dir") or "outputs/agent_sessions"),
        ),
        tools_whitelist=list(tools.get("whitelist") or []),
    )


def get_agent_cfg_dict() -> dict[str, Any]:
    """以原 dict 形态返回配置（供 pi_runtime/_audit_cfg/skills 等按旧键路径消费）。"""
    return get_agent_config().model_dump()


def set_runtime_persisted(rt: str) -> AgentConfig:
    """写回 agent.yaml 的 runtime 字段并失效缓存（供 POST /agent/runtime 使用）。"""
    rt = _validate_runtime(rt)
    cfg = _load_raw()
    cfg["runtime"] = rt
    _write_raw(cfg)
    get_agent_config.cache_clear()
    return get_agent_config()


def get_pi_agent_settings() -> dict[str, Any]:
    """返回 /agent/pi/config 的 settings 段；密钥仅暴露布尔与掩码。"""
    cfg = get_agent_config()
    api_key = get_deepseek_api_key()
    return {
        "runtime": cfg.runtime,
        "llm": {
            "base_url": cfg.llm.base_url,
            "model": cfg.llm.model,
            "timeout_sec": cfg.llm.timeout_sec,
            "api_key_configured": bool(api_key),
            "api_key_preview": _mask_secret(api_key),
        },
        "pi": {
            "executable": cfg.pi.executable,
            "skills_dir": cfg.pi.skills_dir,
            "session_dir": cfg.pi.session_dir,
            "timeout_sec": cfg.pi.timeout_sec,
            "bridge_model": cfg.pi.bridge_model,
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_deepseek_api_key() -> str:
    """读取本项目 DeepSeek Key；仅供后端上游请求使用，不得直接返回给前端。"""
    return _read_dotenv_value(DEEPSEEK_KEY) or os.environ.get(DEEPSEEK_KEY, "")


def update_pi_agent_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """更新 PiAgent 可保存配置；密钥写入本地 .env，明文不进入返回值。"""
    cfg = _load_raw()
    if "runtime" in payload and payload["runtime"] is not None:
        cfg["runtime"] = _validate_runtime(payload["runtime"])

    llm_payload = payload.get("llm") or {}
    if llm_payload:
        llm = cfg.setdefault("llm", {})
        if "base_url" in llm_payload:
            llm["base_url"] = _validate_base_url(llm_payload.get("base_url"))
        if "timeout_sec" in llm_payload and llm_payload.get("timeout_sec") is not None:
            llm["timeout_sec"] = _validate_timeout(
                llm_payload.get("timeout_sec"),
                label="LLM timeout",
                bounds=LLM_TIMEOUT_RANGE,
            )

    pi_payload = payload.get("pi") or {}
    if pi_payload:
        pi = cfg.setdefault("pi", {})
        if "executable" in pi_payload:
            pi["executable"] = _validate_pi_executable(pi_payload.get("executable"))
        if "skills_dir" in pi_payload:
            pi["skills_dir"] = _validate_project_path(pi_payload.get("skills_dir"), label="skills_dir")
        if "session_dir" in pi_payload:
            pi["session_dir"] = _validate_project_path(pi_payload.get("session_dir"), label="session_dir")
        if "timeout_sec" in pi_payload and pi_payload.get("timeout_sec") is not None:
            pi["timeout_sec"] = _validate_timeout(
                pi_payload.get("timeout_sec"),
                label="Pi timeout",
                bounds=PI_TIMEOUT_RANGE,
            )
        if "bridge_model" in pi_payload:
            pi["bridge_model"] = _validate_bridge_model(pi_payload.get("bridge_model"))

    if payload.get("clear_api_key"):
        _write_dotenv_value(DEEPSEEK_KEY, None)
    else:
        api_key = str(payload.get("api_key") or "").strip()
        if api_key:
            if "\n" in api_key or "\r" in api_key:
                raise ValueError("API Key 不能包含换行")
            _write_dotenv_value(DEEPSEEK_KEY, api_key)

    _write_raw(cfg)
    get_agent_config.cache_clear()
    return get_pi_agent_settings()


def clear_agent_config_cache() -> None:
    """测试用：清空配置缓存。"""
    get_agent_config.cache_clear()


def _validate_runtime(value: Any) -> str:
    runtime = str(value or "").strip().lower()
    if runtime not in ALLOWED_RUNTIMES:
        raise ValueError("runtime 仅支持 pi | local | template")
    return runtime


def _validate_timeout(value: Any, *, label: str, bounds: tuple[int, int]) -> int:
    try:
        timeout = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} 必须是整数秒数") from exc
    low, high = bounds
    if timeout < low or timeout > high:
        raise ValueError(f"{label} 必须在 {low}–{high} 秒之间")
    return timeout


def _validate_base_url(value: Any) -> str:
    url = str(value or "").strip().rstrip("/")
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Base URL 仅支持 http/https，例如 https://api.deepseek.com")
    return url


def _validate_bridge_model(value: Any) -> str:
    model = str(value or "").strip()
    if not model or "/" not in model:
        raise ValueError("Bridge Model 必须使用 provider/model 形式，例如 deepseek/deepseek-chat")
    provider, name = model.split("/", 1)
    if not provider.strip() or not name.strip():
        raise ValueError("Bridge Model 必须使用 provider/model 形式，例如 deepseek/deepseek-chat")
    return model


def _relative_to_root(path: Path) -> str:
    root = project_root().resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"路径必须位于项目根目录下: {path}") from exc


def _resolve_under_config_root(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (project_root() / path).resolve()


def _validate_project_path(value: Any, *, label: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{label} 不能为空")
    return _relative_to_root(_resolve_under_config_root(raw))


def _validate_pi_executable(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Pi executable 不能为空")
    path = _resolve_under_config_root(raw)
    root = project_root().resolve()
    pi_root = (root / "tools" / "pi-cli").resolve()
    try:
        path.resolve().relative_to(pi_root)
    except ValueError as exc:
        raise ValueError(f"Pi executable 必须位于 tools/pi-cli/ 下: {raw}") from exc
    return _relative_to_root(path)


def _read_dotenv_value(key: str) -> str:
    path = _dotenv_path()
    if not path.is_file():
        return ""
    prefix = f"{key}="
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.startswith(prefix):
            continue
        return stripped[len(prefix):].strip().strip('"').strip("'")
    return ""


def _write_dotenv_value(key: str, value: str | None) -> None:
    path = _dotenv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    prefix = f"{key}="
    next_lines: list[str] = []
    replaced = False
    for line in lines:
        if line.strip().startswith(prefix):
            if value is not None:
                next_lines.append(f"{key}={value}")
                replaced = True
            continue
        next_lines.append(line)
    if value is not None and not replaced:
        if next_lines and next_lines[-1].strip():
            next_lines.append("")
        next_lines.append(f"{key}={value}")
    path.write_text("\n".join(next_lines).rstrip() + ("\n" if next_lines else ""), encoding="utf-8")
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


def _mask_secret(value: str) -> str | None:
    secret = str(value or "").strip()
    if not secret:
        return None
    if len(secret) <= 8:
        return "已设置（长度较短，已隐藏）"
    return f"{secret[:4]}…{secret[-4:]}"
