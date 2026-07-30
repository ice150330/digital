"""健康检查路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from digital_marketing import __version__
from digital_marketing.api.deps import get_db
from digital_marketing.core.config import get_settings
from digital_marketing.data.db import probe_db
from digital_marketing.schemas.common import Envelope, HealthData
from digital_marketing.services import artifacts as art

router = APIRouter(tags=["health"])


def _probe_artifacts() -> tuple[bool, str | None, str | None]:
    """检查 metrics / 默认模型是否就绪。"""
    try:
        rows = art.list_metrics()
        if not rows:
            return False, None, "尚无 metrics，请运行 python scripts/02_train_classify.py"
        run_id = art.pick_default_run_id()
        run_dir = art.models_dir() / run_id
        if not (run_dir / "model.joblib").is_file():
            return False, run_id, f"默认 run 模型文件缺失: {run_id}"
        return True, run_id, None
    except art.ArtifactError as e:
        return False, None, e.message
    except Exception as e:  # noqa: BLE001
        return False, None, str(e)


@router.get("/health", response_model=Envelope[HealthData])
def health(request: Request, db: Session = Depends(get_db)) -> Envelope[HealthData]:
    """返回服务、数据库与分析产物健康状态。"""
    settings = get_settings()
    request_id = getattr(request.state, "request_id", "unknown")
    db_ok, count, err = probe_db(db)
    artifacts_ok, default_run_id, art_err = _probe_artifacts()

    messages: list[str] = []
    if db_ok and (count or 0) > 0:
        pass
    elif db_ok:
        messages.append(err or "数据库可达但 campaigns 为空，请运行 python scripts/import_campaigns.py")
    else:
        messages.append(err or "数据库不可达，请运行 python scripts/init_db.py")

    if not artifacts_ok and art_err:
        messages.append(art_err)

    if db_ok and (count or 0) > 0 and artifacts_ok:
        status = "ok"
        message = None
    else:
        status = "degraded"
        message = "；".join(messages) if messages else "服务降级"

    data = HealthData(
        status=status,
        app=settings.app_name,
        version=__version__,
        database_ok=db_ok,
        campaigns_count=count,
        artifacts_ok=artifacts_ok,
        default_run_id=default_run_id,
        message=message,
    )
    return Envelope[HealthData](ok=True, data=data, error=None, request_id=request_id)
