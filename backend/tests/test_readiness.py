from collections.abc import Callable

from fastapi.testclient import TestClient

from app.ml.readiness import model as readiness
from app.ml.readiness.synthetic import generate
from tests.conftest import Headers


def test_training_report_has_required_sections() -> None:
    result = readiness.train(generate(400, seed=1), source="synthetic-test")
    report = result["report"]
    assert set(report["cv_roc_auc"]) >= {
        "logistic_regression",
        "random_forest",
        "hist_gradient_boosting",
    }
    assert report["selected"] in report["cv_roc_auc"]
    assert {"accuracy", "f1", "roc_auc", "brier"} <= set(report["holdout"])
    assert "academics_only" in report["ablation"]
    assert report["calibration_table"]
    assert {"department", "gender"} <= set(report["fairness"])
    assert report["version"].startswith("readiness-")


def test_training_is_reproducible() -> None:
    a = readiness.train(generate(300, seed=3), "s")["report"]
    b = readiness.train(generate(300, seed=3), "s")["report"]
    assert a["holdout"] == b["holdout"]
    assert a["data_hash"] == b["data_hash"]


def test_predict_carries_version_and_attributions() -> None:
    out = readiness.predict(
        {"cgpa": 8.5, "backlogs": 0, "problems_solved": 300, "company_type_product": 1}
    )
    assert 0 <= out["probability"] <= 1
    assert out["model_version"].startswith("readiness-")
    assert out["data_source"].startswith("synthetic")
    assert {a["feature"] for a in out["attributions"]} <= set(readiness.FEATURES)


def test_new_data_triggers_rescore_and_diff(
    client: TestClient, make_student: Callable[..., Headers]
) -> None:
    h = make_student(cgpa=6.0, department="CSE")
    first = client.get("/api/v1/me/readiness", headers=h).json()
    assert first["latest"] is not None  # profile update already rescored
    n = len(first["history"])

    client.post(
        "/api/v1/me/coding",
        headers=h,
        json={"platform": "LeetCode", "problems_solved": 600, "contest_rating": 1800},
    )
    client.post(
        "/api/v1/me/projects", headers=h, json={"title": "Distributed cache", "complexity": 3}
    )
    after = client.get("/api/v1/me/readiness", headers=h).json()
    assert len(after["history"]) == n + 2
    latest = after["latest"]
    assert latest["model_version"].startswith("readiness-")
    assert abs(sum(latest["weights"].values()) - 1) < 1e-3
    assert "interview" in latest["components"]["missing"]
    assert after["change"]["score"] is not None
