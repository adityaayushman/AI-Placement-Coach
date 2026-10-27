from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    admin,
    auth,
    coordinator,
    health,
    interviews,
    learning,
    privacy,
    readiness,
    resumes,
    students,
)
from app.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import (
    METRICS,
    MetricsMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    from app.db.base import Base
    from app.db.session import get_engine, get_sessionmaker
    from app.seed import seed

    # Idempotent: creates missing tables only. Schema changes go through Alembic.
    Base.metadata.create_all(get_engine())
    with get_sessionmaker()() as db:
        seed(db)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="AI Placement Coach API", version="0.2.0", lifespan=lifespan)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RateLimitMiddleware, per_minute=settings.auth_rate_limit_per_minute)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(RequestIdMiddleware)
    for module in (
        health,
        auth,
        students,
        privacy,
        resumes,
        learning,
        interviews,
        readiness,
        coordinator,
        admin,
    ):
        app.include_router(module.router, prefix="/api/v1")

    @app.get("/api/v1/metrics", tags=["health"])
    def metrics() -> dict[str, object]:
        return METRICS.snapshot()

    return app


app = create_app()
