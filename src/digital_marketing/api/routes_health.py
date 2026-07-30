"""健康检查路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from digital_marketing import __version__
from digital_marketing.api.deps import get_db
from digital_marketing.core.config import get_settings
from digital_marketing.data.db import probe_db
from digital_marketing.schemas.common import Envelope, HealthData

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Envelope[HealthData])
def health(request: Request, db: Session = Depends(get_db)) -> Envelope[HealthData]:
    """返回服务与数据库健康状态。"""
    settings = get_settings()
    request_id = getattr(request.state, "request_id", "unknown")
    db_ok, count, err = probe_db(db)

    if db_ok and (count or 0) > 0:
        status = "ok"
        message = None
    elif db_ok:
        status = "degraded"
        message = err or "数据库可达但 campaigns 为空，请运行 python scripts/import_campaigns.py"
    else:
        status = "degraded"
        message = err or "数据库不可达，请运行 python scripts/init_db.py"

    data = HealthData(
        status=status,
        app=settings.app_name,
        version=__version__,
        database_ok=db_ok,
        campaigns_count=count,
        message=message,
    )
    return Envelope[HealthData](ok=True, data=data, error=None, request_id=request_id)
