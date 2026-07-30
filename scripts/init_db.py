#!/usr/bin/env python3
"""初始化 SQLite 表结构。"""

from __future__ import annotations

import sys
from pathlib import Path

# 允许未 editable 安装时直接运行
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from digital_marketing.core.logging import setup_logging  # noqa: E402
from digital_marketing.core.config import get_settings  # noqa: E402
from digital_marketing.data.db import init_db  # noqa: E402


def main() -> int:
    setup_logging()
    settings = get_settings()
    path = init_db(settings)
    print(f"数据库已初始化: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
