from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from tests.conftest import Headers
from tests.fixtures import STRONG_RESUME


def _upload(client: TestClient, h: Headers) -> int:
    r = client.post(
        "/api/v1/resumes",
        headers=h,
        files={"file": ("cv.txt", STRONG_RESUME.encode(), "text/plain")},
    )
    return r.status_code


def test_resume_requires_consent_and_revoke_blocks_access(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student(consents=())
    assert _upload(client, h) == 403
    client.put("/api/v1/consents", headers=h, json=[{"scope": "resume", "granted": True}])
    assert _upload(client, h) == 201
    assert client.get("/api/v1/resumes", headers=h).status_code == 200

    client.put("/api/v1/consents", headers=h, json=[{"scope": "resume", "granted": False}])
    assert client.get("/api/v1/resumes", headers=h).status_code == 403
    assert client.get("/api/v1/resumes/analyses/latest", headers=h).status_code == 403
    states = {c["scope"]: c["granted"] for c in client.get("/api/v1/consents", headers=h).json()}
    assert states["resume"] is False


def test_unknown_consent_scope_rejected(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student()
    r = client.put("/api/v1/consents", headers=h, json=[{"scope": "telepathy", "granted": True}])
    assert r.status_code == 422


def test_export_contains_my_data(client: TestClient, make_student: Callable[..., Headers]) -> None:
    h = make_student(cgpa=7.5)
    client.post("/api/v1/me/projects", headers=h, json={"title": "Chat app", "tech": ["react"]})
    data = client.get("/api/v1/me/export", headers=h).json()
    assert data["student_profiles"][0]["cgpa"] == 7.5
    assert data["projects"][0]["title"] == "Chat app"
    csv = client.get("/api/v1/me/export?format=csv", headers=h)
    assert csv.headers["content-type"].startswith("text/csv")


def test_delete_all_my_data_purges_rows_and_files(
    client: TestClient, make_student: Callable[..., Headers], admin: Headers
) -> None:
    h = make_student()
    assert _upload(client, h) == 201
    storage = Path(get_settings().storage_dir)
    before = set(storage.iterdir())
    assert before

    assert client.delete("/api/v1/me", headers=h).status_code == 204
    assert len(set(storage.iterdir())) == len(before) - 1
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
    actions = [a["action"] for a in client.get("/api/v1/admin/audit", headers=admin).json()]
    assert "student_deleted_all_data" in actions


def test_coordinator_sees_only_consented_individuals(
    client: TestClient, make_student: Callable[..., Headers], coordinator: Headers
) -> None:
    visible = make_student(consents=("coordinator_visibility",), department="CSE")
    make_student(consents=(), department="CSE")
    me = client.get("/api/v1/auth/me", headers=visible).json()
    rows = client.get("/api/v1/coordinator/students", headers=coordinator).json()
    ids = {r["user_id"] for r in rows}
    assert me["id"] in ids
    # Revoking removes the student from the individual view.
    client.put(
        "/api/v1/consents",
        headers=visible,
        json=[{"scope": "coordinator_visibility", "granted": False}],
    )
    ids = {
        r["user_id"] for r in client.get("/api/v1/coordinator/students", headers=coordinator).json()
    }
    assert me["id"] not in ids
