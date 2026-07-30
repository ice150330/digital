"""FastAPI 依赖。"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from digital_marketing.data.db import get_db as _get_db


def get_db() -> Generator[Session, None, None]:
    """数据库会话依赖。"""
    yield from _get_db()
