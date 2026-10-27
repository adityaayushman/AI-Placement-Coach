import os
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="pc-tests-"))
os.environ.update(
    {
        "DATABASE_URL": f"sqlite:///{(_TMP / 'test.db').as_posix()}",
        "STORAGE_DIR": str(_TMP / "storage"),
        "MODEL_DIR": str(_TMP / "models"),
        "JOBS_INLINE": "true",
        "SYNTHETIC_ROWS": "400",
        "AUTH_RATE_LIMIT_PER_MINUTE": "1000",
        "SECRET_KEY": "test-secret-key-with-enough-length-for-hs256",
        "ADMIN_EMAIL": "admin@example.com",
        "ADMIN_PASSWORD": "admin-pass-123",
    }
)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

Headers = dict[str, str]


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


_counter = iter(range(10_000))


@pytest.fixture
def make_student(client: TestClient) -> Callable[..., Headers]:
    def make(
        consents: tuple[str, ...] = ("resume", "interview_recording", "analytics"),
        **profile: object,
    ) -> Headers:
        email = f"student{next(_counter)}@example.com"
        r = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "password123", "full_name": "Test"},
        )
        assert r.status_code == 201, r.text
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        if consents:
            body = [{"scope": s, "granted": True} for s in consents]
            assert client.put("/api/v1/consents", json=body, headers=h).status_code == 200
        if profile:
            assert client.put("/api/v1/me/profile", json=profile, headers=h).status_code == 200
        return h

    return make


def login(client: TestClient, email: str, password: str) -> Headers:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client: TestClient) -> Headers:
    return login(client, "admin@example.com", "admin-pass-123")


@pytest.fixture
def coordinator(client: TestClient, admin: Headers) -> Headers:
    email = f"coord{next(_counter)}@example.com"
    r = client.post(
        "/api/v1/admin/users",
        headers=admin,
        json={"email": email, "password": "coordpass1", "role": "coordinator"},
    )
    assert r.status_code == 201, r.text
    return login(client, email, "coordpass1")
