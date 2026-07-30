"""从只读 CSV 导入营销主数据到 SQLite。"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from digital_marketing.data.models import Campaign, ImportBatch, utc_now

logger = logging.getLogger(__name__)

# CSV 表头（权威顺序）
EXPECTED_COLUMNS = [
    "CustomerID",
    "Age",
    "Gender",
    "Income",
    "CampaignChannel",
    "CampaignType",
    "AdSpend",
    "ClickThroughRate",
    "ConversionRate",
    "WebsiteVisits",
    "PagesPerVisit",
    "TimeOnSite",
    "SocialShares",
    "EmailOpens",
    "EmailClicks",
    "PreviousPurchases",
    "LoyaltyPoints",
    "AdvertisingPlatform",
    "AdvertisingTool",
    "Conversion",
]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_columns(df: pd.DataFrame) -> None:
    cols = list(df.columns)
    missing = [c for c in EXPECTED_COLUMNS if c not in cols]
    if missing:
        raise ValueError(f"CSV 缺少列: {missing}")
    extra = [c for c in cols if c not in EXPECTED_COLUMNS]
    if extra:
        logger.warning("CSV 含未识别列（将忽略）: %s", extra)


def _row_to_campaign(row: pd.Series, imported_at) -> Campaign:
    return Campaign(
        customer_id=int(row["CustomerID"]),
        age=int(row["Age"]),
        gender=str(row["Gender"]),
        income=float(row["Income"]),
        campaign_channel=str(row["CampaignChannel"]),
        campaign_type=str(row["CampaignType"]),
        ad_spend=float(row["AdSpend"]),
        click_through_rate=float(row["ClickThroughRate"]),
        conversion_rate=float(row["ConversionRate"]),
        website_visits=int(row["WebsiteVisits"]),
        pages_per_visit=float(row["PagesPerVisit"]),
        time_on_site=float(row["TimeOnSite"]),
        social_shares=int(row["SocialShares"]),
        email_opens=int(row["EmailOpens"]),
        email_clicks=int(row["EmailClicks"]),
        previous_purchases=int(row["PreviousPurchases"]),
        loyalty_points=int(row["LoyaltyPoints"]),
        advertising_platform=str(row["AdvertisingPlatform"]),
        advertising_tool=str(row["AdvertisingTool"]),
        conversion=int(row["Conversion"]),
        imported_at=imported_at,
    )


def import_campaigns_from_csv(
    session: Session,
    csv_path: Path,
    *,
    force: bool = True,
) -> ImportBatch:
    """将 CSV 导入 campaigns 表。

    force=True 时先清空 campaigns 再全量写入（默认策略）。
    不修改 csv_path 文件本身。
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV 不存在: {csv_path}")

    digest = file_sha256(csv_path)
    df = pd.read_csv(csv_path)
    validate_columns(df)
    df = df[EXPECTED_COLUMNS]

    if force:
        session.execute(delete(Campaign))
        session.flush()

    now = utc_now()
    campaigns = [_row_to_campaign(row, now) for _, row in df.iterrows()]
    session.add_all(campaigns)

    batch = ImportBatch(
        source_path=str(csv_path.resolve()),
        row_count=len(campaigns),
        file_sha256=digest,
        created_at=now,
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)
    logger.info("已导入 %s 行 → campaigns（sha256=%s…）", batch.row_count, digest[:12])
    return batch
