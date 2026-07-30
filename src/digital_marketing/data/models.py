"""SQLAlchemy 模型。

注意：customer_id 可查询存储，但后续特征工程 / 入模时必须排除（AGENTS 红线）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """声明式基类。"""


class Campaign(Base):
    """营销活动行（对应 CSV 一行）。"""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # CustomerID：业务可查，永不入模
    customer_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    income: Mapped[float] = mapped_column(Float, nullable=False)
    campaign_channel: Mapped[str] = mapped_column(String(64), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ad_spend: Mapped[float] = mapped_column(Float, nullable=False)
    click_through_rate: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_rate: Mapped[float] = mapped_column(Float, nullable=False)
    website_visits: Mapped[int] = mapped_column(Integer, nullable=False)
    pages_per_visit: Mapped[float] = mapped_column(Float, nullable=False)
    time_on_site: Mapped[float] = mapped_column(Float, nullable=False)
    social_shares: Mapped[int] = mapped_column(Integer, nullable=False)
    email_opens: Mapped[int] = mapped_column(Integer, nullable=False)
    email_clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_purchases: Mapped[int] = mapped_column(Integer, nullable=False)
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False)
    advertising_platform: Mapped[str] = mapped_column(String(64), nullable=False)
    advertising_tool: Mapped[str] = mapped_column(String(64), nullable=False)
    conversion: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ImportBatch(Base):
    """CSV 导入批次元数据。"""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
