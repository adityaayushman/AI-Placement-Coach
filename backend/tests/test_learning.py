from collections.abc import Callable

from fastapi.testclient import TestClient

from app.ml.knowledge import bkt
from app.ml.knowledge.recommender import rank
from tests.conftest import Headers


def test_bkt_moves_in_the_right_direction() -> None:
    p = bkt.DEFAULT.p_init
    up = bkt.update(p, True)
    down = bkt.update(p, False)
    assert down < p < up <= 1
    for _ in range(10):
        p = bkt.update(p, True)
    assert p > 0.95


def test_offline_replay_recommendations_shift_after_mastery() -> None:
    """Replay a synthetic event stream: a student masters DSA, so DSA leaves the top picks."""
    skills = ["data structures", "algorithms", "system design", "dbms", "aptitude"]
    mastery: dict[str, float] = {}
    first = [r.skill for r in rank(mastery, skills, "product")]
    assert first[0] in {"data structures", "algorithms"}
    for _ in range(8):
        for s in ("data structures", "algorithms"):
            mastery[s] = bkt.update(mastery.get(s, bkt.DEFAULT.p_init), True)
    after = [r.skill for r in rank(mastery, skills, "product")]
    assert "data structures" not in after and "algorithms" not in after
    assert after != first


def test_prerequisites_and_ignores_lower_priority() -> None:
    base = {r.skill: r.priority for r in rank({}, ["dynamic programming", "recursion"], "product")}
    ready = {
        r.skill: r.priority
        for r in rank({"algorithms": 0.85, "recursion": 0.85}, ["dynamic programming"], "product")
    }
    assert ready["dynamic programming"] > base["dynamic programming"]
    ignored = {
        r.skill: r.priority
        for r in rank({}, ["dynamic programming", "recursion"], "product", ignored={"recursion": 1})
    }
    assert ignored["recursion"] < base["recursion"]


def test_quiz_attempt_updates_mastery_events_and_recommendations(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student(target_company_type="product")
    assessments = client.get("/api/v1/assessments", headers=h).json()
    dsa = next(a for a in assessments if a["skill"] == "data structures")
    detail = client.get(f"/api/v1/assessments/{dsa['id']}", headers=h).json()
    assert all("answer_index" not in q for q in detail["questions"])  # never leak answers

    before = [r["skill"] for r in client.get("/api/v1/me/recommendations", headers=h).json()]
    from app.seed import QUIZZES

    correct = {
        q["id"]: next(a for p, _, a in QUIZZES["data structures"] if p == q["prompt"])
        for q in detail["questions"]
    }
    for _ in range(4):
        r = client.post(
            f"/api/v1/assessments/{dsa['id']}/attempts", headers=h, json={"answers": correct}
        )
        assert r.status_code == 201
        assert r.json()["score"] == 100.0

    mastery = {m["skill"]: m["p_known"] for m in client.get("/api/v1/me/mastery", headers=h).json()}
    assert mastery["data structures"] > 0.85
    after = [r["skill"] for r in client.get("/api/v1/me/recommendations", headers=h).json()]
    assert "data structures" not in after
    assert before != after

    export = client.get("/api/v1/me/export", headers=h).json()
    assert any(e["type"] == "assessment_attempted" for e in export["events"])


def test_recommendation_feedback_loop(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student()
    recs = client.get("/api/v1/me/recommendations", headers=h).json()
    assert recs and all(r["reason"] for r in recs)
    target = recs[0]
    r = client.patch(
        f"/api/v1/me/recommendations/{target['id']}", headers=h, json={"status": "ignored"}
    )
    assert r.status_code == 200
    open_ids = {x["id"] for x in client.get("/api/v1/me/recommendations", headers=h).json()}
    assert target["id"] not in open_ids


def test_no_events_without_analytics_consent(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student(consents=())
    client.post(
        "/api/v1/me/coding", headers=h, json={"platform": "LeetCode", "problems_solved": 50}
    )
    assert client.get("/api/v1/me/export", headers=h).json()["events"] == []


def test_coding_csv_import(client: TestClient, make_student: Callable[..., Headers]) -> None:
    h = make_student()
    csv = b"platform,problems_solved,contest_rating\nLeetCode,120,1500\nCodeforces,40,\n"
    r = client.post(
        "/api/v1/me/coding/import", headers=h, files={"file": ("c.csv", csv, "text/csv")}
    )
    assert r.status_code == 201
    assert len(r.json()) == 2
    bad = client.post(
        "/api/v1/me/coding/import",
        headers=h,
        files={"file": ("c.csv", b"foo,bar\n1,2\n", "text/csv")},
    )
    assert bad.status_code == 422
