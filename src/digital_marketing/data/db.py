"""SQLite 引擎与会话。"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from digital_marketing.core.config import Settings, get_settings
from digital_marketing.core.paths import ensure_dir
from digital_marketing.data.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _sqlite_pragma(dbapi_conn, _connection_record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine(settings: Settings | None = None, *, force_new: bool = False) -> Engine:
    """获取全局（或强制新建）引擎。"""
    global _engine, _SessionLocal
    if _engine is not None and not force_new:
        return _engine

    cfg = settings or get_settings()
    ensure_dir(cfg.db_path.parent)
    engine = create_engine(
        cfg.sqlalchemy_url(),
        echo=cfg.database_echo,
        future=True,
        connect_args={"check_same_thread": False},
    )
    if engine.url.get_backend_name() == "sqlite":
        event.listen(engine, "connect", _sqlite_pragma)

    if force_new:
        return engine

    _engine = engine
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    """返回 sessionmaker。"""
    global _SessionLocal
    if _SessionLocal is None:
        get_engine(settings)
    assert _SessionLocal is not None
    return _SessionLocal


def reset_engine() -> None:
    """测试用：释放全局引擎。"""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def init_db(settings: Settings | None = None) -> Path:
    """创建表结构，返回数据库文件路径。"""
    cfg = settings or get_settings()
    engine = get_engine(cfg)
    Base.metadata.create_all(bind=engine)
    return cfg.db_path


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：请求级 Session。"""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def probe_db(db: Session) -> tuple[bool, int | None, str | None]:
    """探测数据库是否可用，返回 (ok, campaigns_count, error_message)。"""
    try:
        db.execute(text("SELECT 1"))
        # 表可能尚未创建
        try:
            count = db.execute(text("SELECT COUNT(*) FROM campaigns")).scalar_one()
            return True, int(count), None
        except Exception:
            return True, 0, "表 campaigns 尚未就绪，请运行 python scripts/init_db.py"
    except Exception as exc:  # noqa: BLE001 — 健康检查需吞并并报告
        return False, None, str(exc)
