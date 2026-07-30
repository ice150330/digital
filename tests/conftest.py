"""pytest 公共夹具：临时 SQLite 与测试客户端。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from digital_marketing.core.config import clear_settings_cache, get_settings
from digital_marketing.data.db import get_engine, init_db, reset_engine
from digital_marketing.data.import_csv import import_campaigns_from_csv
from digital_marketing.data.models import Base


@pytest.fixture()
def tmp_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """使用临时库并重置全局引擎/配置。"""
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DIGITAL_DATABASE_URL", url)
    # 确保项目根可解析
    root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("DIGITAL_ROOT", str(root))
    clear_settings_cache()
    reset_engine()
    yield db_path
    reset_engine()
    clear_settings_cache()
    monkeypatch.delenv("DIGITAL_DATABASE_URL", raising=False)


@pytest.fixture()
def db_session(tmp_db_path: Path):
    settings = get_settings()
    init_db(settings)
    engine = get_engine(settings)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with factory() as session:
        yield session


@pytest.fixture()
def sample_csv(tmp_path: Path) -> Path:
    """迷你 CSV（3 行）用于导入测试。"""
    content = (
        "CustomerID,Age,Gender,Income,CampaignChannel,CampaignType,AdSpend,"
        "ClickThroughRate,ConversionRate,WebsiteVisits,PagesPerVisit,TimeOnSite,"
        "SocialShares,EmailOpens,EmailClicks,PreviousPurchases,LoyaltyPoints,"
        "AdvertisingPlatform,AdvertisingTool,Conversion\n"
        "1,30,Female,50000,Email,Awareness,100.0,0.1,0.2,5,2.0,3.0,1,2,1,0,100,IsConfid,ToolConfid,1\n"
        "2,40,Male,60000,PPC,Conversion,200.0,0.2,0.1,10,3.0,4.0,2,3,2,1,200,IsConfid,ToolConfid,0\n"
        "3,50,Female,70000,SEO,Retention,150.0,0.15,0.15,0,1.0,2.0,0,1,0,2,300,IsConfid,ToolConfid,1\n"
    )
    path = tmp_path / "sample.csv"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def client(tmp_db_path: Path, sample_csv: Path):
    """带已导入数据的 TestClient。"""
    settings = get_settings()
    init_db(settings)
    engine = get_engine(settings)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with factory() as session:
        import_campaigns_from_csv(session, sample_csv, force=True)

    # 延迟导入，确保 env 已设置
    from digital_marketing.api.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
