from collections.abc import Callable

from fastapi.testclient import TestClient

from tests.conftest import Headers


def test_register_login_refresh_me(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/register", json={"email": "Alice@Example.com", "password": "password123"}
    )
    assert r.status_code == 201
    tokens = r.json()
    assert tokens["role"] == "student"

    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.json()["email"] == "alice@example.com"

    assert (
        client.post(
            "/api/v1/auth/register", json={"email": "alice@example.com", "password": "password123"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "alice@example.com", "password": "wrong-pass"}
        ).status_code
        == 401
    )
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200


def test_refresh_token_cannot_be_used_as_access(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/register", json={"email": "bob@example.com", "password": "password123"}
    )
    refresh = r.json()["refresh_token"]
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}).status_code
        == 401
    )


def test_unauthenticated_is_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/me/profile").status_code == 401
    assert client.get("/api/v1/coordinator/cohort").status_code == 401


def test_student_cannot_use_staff_endpoints(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student()
    assert client.get("/api/v1/coordinator/cohort", headers=h).status_code == 403
    assert client.get("/api/v1/admin/audit", headers=h).status_code == 403
    assert (
        client.post(
            "/api/v1/jobs", headers=h, json={"company": "x", "role": "y", "text": "z"}
        ).status_code
        == 403
    )


def test_coordinator_is_not_admin(client: TestClient, coordinator: Headers) -> None:
    assert client.get("/api/v1/coordinator/cohort", headers=coordinator).status_code == 200
    assert client.get("/api/v1/admin/audit", headers=coordinator).status_code == 403
    assert client.get("/api/v1/me/profile", headers=coordinator).status_code == 403


def test_profile_validation(client: TestClient, make_student: Callable[..., Headers]) -> None:
    h = make_student()
    assert client.put("/api/v1/me/profile", headers=h, json={"cgpa": 11}).status_code == 422
    r = client.put(
        "/api/v1/me/profile",
        headers=h,
        json={"cgpa": 8.1, "department": "CSE", "target_company_type": "service"},
    )
    assert r.status_code == 200
    assert r.json()["cgpa"] == 8.1
    assert len(r.json()["pseudonym_id"]) == 32
