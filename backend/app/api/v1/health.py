from fastapi import APIRouter, Response, status
from sqlalchemy import create_engine, text

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up. No dependency checks."""
    return {"status": "ok"}


def _check_db(url: str) -> bool:
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


def _check_redis(url: str) -> bool:
    try:
        import redis

        return bool(redis.Redis.from_url(url, socket_connect_timeout=2).ping())
    except Exception:
        return False


@router.get("/ready")
def ready(response: Response) -> dict[str, str]:
    """Readiness: DB and Redis reachable."""
    s = get_settings()
    checks = {"db": _check_db(s.database_url), "redis": _check_redis(s.redis_url)}
    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {k: "ok" if v else "down" for k, v in checks.items()}
