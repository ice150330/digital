"""FastAPI 应用入口。"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from digital_marketing import __version__
from digital_marketing.api.routes_agent import router as agent_router
from digital_marketing.api.routes_data import router as data_router
from digital_marketing.api.routes_explain import router as explain_router
from digital_marketing.api.routes_health import router as health_router
from digital_marketing.api.routes_models import router as models_router
from digital_marketing.api.routes_rules import router as rules_router
from digital_marketing.api.routes_segments import router as segments_router
from digital_marketing.api.routes_simulate import router as simulate_router
from digital_marketing.core.config import get_settings
from digital_marketing.core.logging import setup_logging
from digital_marketing.schemas.common import ApiError, Envelope


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="数字营销转化分析 API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        body = Envelope(
            ok=False,
            data=None,
            error=ApiError(
                code="INTERNAL_ERROR",
                message="服务器内部错误",
                detail={"type": type(exc).__name__},
            ),
            request_id=request_id,
        )
        return JSONResponse(status_code=500, content=body.model_dump())

    prefix = settings.api_prefix.rstrip("/") or "/api/v1"
    app.include_router(health_router, prefix=prefix)
    app.include_router(data_router, prefix=prefix)
    app.include_router(models_router, prefix=prefix)
    app.include_router(explain_router, prefix=prefix)
    app.include_router(segments_router, prefix=prefix)
    app.include_router(rules_router, prefix=prefix)
    app.include_router(simulate_router, prefix=prefix)
    app.include_router(agent_router, prefix=prefix)
    return app


app = create_app()
