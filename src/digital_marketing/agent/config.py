"""Agent 统一配置：config/agent.yaml 单一加载点（缓存 + pydantic 校验）。

Stage 1 收敛：local_runtime / pi_runtime / audit / routes_agent 不再各自
yaml.safe_load，一律经 get_agent_config()；写回 runtime 经 set_runtime_persisted()
并自动失效缓存。缓存范式复刻 core/config.py::get_settings。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml
from pydantic import BaseModel, Field

from digital_marketing.core.paths import project_root


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


def _load_raw() -> dict[str, Any]:
    path = _agent_yaml_path()
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


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
    path = _agent_yaml_path()
    cfg = _load_raw()
    cfg["runtime"] = rt
    path.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    get_agent_config.cache_clear()
    return get_agent_config()


def clear_agent_config_cache() -> None:
    """测试用：清空配置缓存。"""
    get_agent_config.cache_clear()
