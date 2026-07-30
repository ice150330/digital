"""CSV → SQLite 导入测试。"""

from __future__ import annotations

from sqlalchemy import func, select

from digital_marketing.data.import_csv import import_campaigns_from_csv
from digital_marketing.data.models import Campaign, ImportBatch


def test_import_campaigns_count(db_session, sample_csv):
    batch = import_campaigns_from_csv(db_session, sample_csv, force=True)
    assert batch.row_count == 3
    assert len(batch.file_sha256) == 64

    n = db_session.scalar(select(func.count()).select_from(Campaign))
    assert n == 3

    batches = db_session.scalars(select(ImportBatch)).all()
    assert len(batches) >= 1


def test_import_force_rebuild(db_session, sample_csv):
    import_campaigns_from_csv(db_session, sample_csv, force=True)
    import_campaigns_from_csv(db_session, sample_csv, force=True)
    n = db_session.scalar(select(func.count()).select_from(Campaign))
    assert n == 3


def test_customer_id_stored(db_session, sample_csv):
    import_campaigns_from_csv(db_session, sample_csv, force=True)
    row = db_session.scalar(select(Campaign).where(Campaign.customer_id == 2))
    assert row is not None
    assert row.conversion == 0
    assert row.campaign_channel == "PPC"
