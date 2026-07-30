"""Pi 路径硬约束：必须在 tools/pi-cli/。"""

from __future__ import annotations

import pytest

from digital_marketing.agent.pi_runtime import PiPathError, pi_executable_path, pi_status
from digital_marketing.core.paths import project_root


def test_pi_executable_under_tools_pi_cli():
    path = pi_executable_path()
    root = project_root().resolve()
    path.resolve().relative_to((root / "tools" / "pi-cli").resolve())
    assert "pi-cli" in path.parts


def test_pi_status_valid_prefix():
    st = pi_status()
    assert st["valid_prefix"] is True
    assert "executable" in st


def test_pi_path_rejects_outside(monkeypatch, tmp_path):
    """伪造配置指向 tools 外时应抛错。"""
    import digital_marketing.agent.pi_runtime as pr

    cfg_path = project_root() / "config" / "agent.yaml"
    original = cfg_path.read_text(encoding="utf-8") if cfg_path.is_file() else ""

    def fake_cfg():
        return {"pi": {"executable": "C:/Windows/System32/pi.exe"}}

    monkeypatch.setattr(pr, "_agent_cfg", fake_cfg)
    with pytest.raises(PiPathError):
        pr.pi_executable_path()
