from collections.abc import Callable

from fastapi.testclient import TestClient

from tests.conftest import Headers


def test_cohort_aggregates_and_small_group_suppression(
    client: TestClient, make_student: Callable[..., Headers], coordinator: Headers
) -> None:
    for _ in range(3):
        make_student(department="ECE-cohort", cgpa=7.0)
    make_student(department="Tiny-dept", cgpa=7.0)
    cohort = client.get("/api/v1/coordinator/cohort", headers=coordinator).json()
    depts = {d["department"]: d for d in cohort["departments"]}
    assert depts["ECE-cohort"]["suppressed"] is False
    assert depts["ECE-cohort"]["score"] is not None
    assert depts["Tiny-dept"]["suppressed"] is True
    assert "score" not in depts["Tiny-dept"]
    assert sum(b["count"] for b in cohort["distribution"]) == cohort["scored"]


def test_csv_export_is_consented_only_and_audited(
    client: TestClient, make_student: Callable[..., Headers], coordinator: Headers, admin: Headers
) -> None:
    make_student(consents=("coordinator_visibility",))
    hidden = make_student(consents=())
    hidden_email = client.get("/api/v1/auth/me", headers=hidden).json()["email"]
    r = client.get("/api/v1/coordinator/students.csv", headers=coordinator)
    assert r.status_code == 200
    assert hidden_email not in r.text
    actions = [a["action"] for a in client.get("/api/v1/admin/audit", headers=admin).json()]
    assert "coordinator_exported_csv" in actions


def test_announcements(
    client: TestClient, coordinator: Headers, make_student: Callable[..., Headers]
) -> None:
    r = client.post(
        "/api/v1/announcements",
        headers=coordinator,
        json={"title": "Drive on Friday", "body": "Bring your ID."},
    )
    assert r.status_code == 201
    h = make_student()
    titles = [a["title"] for a in client.get("/api/v1/announcements", headers=h).json()]
    assert "Drive on Friday" in titles
    assert (
        client.post(
            "/api/v1/announcements", headers=h, json={"title": "x", "body": "y"}
        ).status_code
        == 403
    )
