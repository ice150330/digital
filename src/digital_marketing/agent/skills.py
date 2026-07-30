"""项目内 Pi skills 发现：扫描 skills_dir 下的 */SKILL.md 并解析 frontmatter。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from digital_marketing.core.paths import project_root

DEFAULT_SKILLS_DIR = "src/digital_marketing/agent/skills"


def skills_dir(cfg: dict[str, Any] | None = None) -> Path:
    rel = DEFAULT_SKILLS_DIR
    if cfg:
        rel = str((cfg.get("pi") or {}).get("skills_dir") or DEFAULT_SKILLS_DIR)
    root = project_root()
    path = (root / rel).resolve()
    # 技能目录也必须在项目内
    path.relative_to(root.resolve())
    return path


def list_skills(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """返回 [{name, description, path}]；目录缺失时为空列表。"""
    d = skills_dir(cfg)
    if not d.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for skill_md in sorted(d.glob("*/SKILL.md")):
        name = skill_md.parent.name
        description = ""
        try:
            text = skill_md.read_text(encoding="utf-8")
            if text.startswith("---"):
                _, fm, _ = text.split("---", 2)
                meta = yaml.safe_load(fm) or {}
                name = str(meta.get("name") or name)
                description = str(meta.get("description") or "")
        except Exception:  # noqa: BLE001 — 单个 skill 解析失败不影响列表
            pass
        out.append({"name": name, "description": description, "path": str(skill_md)})
    return out
