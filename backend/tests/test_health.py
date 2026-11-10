from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_request_id_generated_and_echoed() -> None:
    assert client.get("/api/v1/health").headers["X-Request-ID"]
    r = client.get("/api/v1/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"


def test_ready_ok_when_dependencies_up() -> None:
    with (
        patch("app.api.v1.health._check_db", return_value=True),
        patch("app.api.v1.health._check_redis", return_value=True),
    ):
        r = client.get("/api/v1/ready")
    assert r.status_code == 200
    assert r.json() == {"db": "ok"}  # tests run with JOBS_INLINE, so Redis is not required


def test_ready_503_when_dependency_down() -> None:
    with (
        patch("app.api.v1.health._check_db", return_value=False),
        patch("app.api.v1.health._check_redis", return_value=True),
    ):
        r = client.get("/api/v1/ready")
    assert r.status_code == 503
    assert r.json() == {"db": "down"}


def test_ready_checks_redis_when_a_worker_queue_is_used() -> None:
    from types import SimpleNamespace

    settings = SimpleNamespace(database_url="sqlite://", redis_url="redis://x", jobs_inline=False)
    with (
        patch("app.api.v1.health.get_settings", return_value=settings),
        patch("app.api.v1.health._check_redis", return_value=False),
    ):
        r = client.get("/api/v1/ready")
    assert r.status_code == 503
    assert r.json() == {"db": "ok", "redis": "down"}
