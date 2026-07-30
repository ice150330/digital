"""加载 config/settings.yaml 与环境变量覆盖。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from digital_marketing.core.paths import project_root, resolve_under_root


@dataclass
class Settings:
    """运行时配置快照。"""

    app_name: str = "digital-marketing"
    app_version: str = "0.1.0"
    env: str = "dev"
    seed: int = 42
    raw_csv: Path = field(default_factory=lambda: resolve_under_root("data/digital_marketing_campaign_dataset.csv"))
    outputs_dir: Path = field(default_factory=lambda: resolve_under_root("outputs"))
    db_path: Path = field(default_factory=lambda: resolve_under_root("outputs/db/app.db"))
    database_url: str | None = None
    database_echo: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )

    def sqlalchemy_url(self) -> str:
        """返回 SQLAlchemy 连接串（默认同步 sqlite）。"""
        if self.database_url:
            return self.database_url
        # Windows 路径需用正斜杠
        db = self.db_path.resolve().as_posix()
        return f"sqlite:///{db}"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是映射: {path}")
    return data


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """加载并缓存 Settings。"""
    load_dotenv(project_root() / ".env", override=False)
    raw = _load_yaml(project_root() / "config" / "settings.yaml")

    app = raw.get("app") or {}
    paths = raw.get("paths") or {}
    database = raw.get("database") or {}
    api = raw.get("api") or {}

    raw_csv = paths.get("raw_csv", "data/digital_marketing_campaign_dataset.csv")
    outputs_dir = paths.get("outputs_dir", "outputs")
    db_rel = database.get("path") or paths.get("db_filename")
    if not db_rel or db_rel == paths.get("db_filename"):
        db_dir = paths.get("db_dir", "outputs/db")
        db_name = paths.get("db_filename", "app.db")
        db_rel = f"{db_dir}/{db_name}" if not database.get("path") else database["path"]

    settings = Settings(
        app_name=str(app.get("name", "digital-marketing")),
        app_version=str(app.get("version", "0.1.0")),
        env=str(app.get("env", "dev")),
        seed=int(raw.get("seed", 42)),
        raw_csv=resolve_under_root(str(raw_csv)),
        outputs_dir=resolve_under_root(str(outputs_dir)),
        db_path=resolve_under_root(str(db_rel)),
        database_url=os.environ.get("DIGITAL_DATABASE_URL") or None,
        database_echo=bool(database.get("echo", False)),
        api_prefix=str(api.get("prefix", "/api/v1")),
        cors_origins=list(api.get("cors_origins") or [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]),
    )
    return settings


def clear_settings_cache() -> None:
    """测试用：清空配置缓存。"""
    get_settings.cache_clear()
