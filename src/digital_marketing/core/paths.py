"""项目路径解析（禁止写死本机绝对路径）。"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

# 用于上溯识别项目根的锚点文件
_ROOT_MARKERS = ("pyproject.toml", "AGENTS.md")


@lru_cache(maxsize=1)
def project_root() -> Path:
    """解析项目根目录。

    优先环境变量 DIGITAL_ROOT；否则从本文件上溯查找 pyproject.toml / AGENTS.md。
    """
    env = os.environ.get("DIGITAL_ROOT", "").strip()
    if env:
        root = Path(env).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"DIGITAL_ROOT 不是有效目录: {root}")
        return root

    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if any((parent / marker).exists() for marker in _ROOT_MARKERS):
            return parent

    # 兜底：src/digital_marketing/core → 上三级到仓库根
    return here.parents[3]


def resolve_under_root(relative: str | Path) -> Path:
    """将相对路径解析为项目根下的绝对路径。"""
    path = Path(relative)
    if path.is_absolute():
        return path.resolve()
    return (project_root() / path).resolve()


def ensure_dir(path: Path) -> Path:
    """确保目录存在并返回。"""
    path.mkdir(parents=True, exist_ok=True)
    return path
