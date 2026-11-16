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


def test_real_dataset_matches_schema() -> None:
    """The bundled real (third-party, CC0) campus placement dataset ships with the backend and
    lines up with the model's feature schema. See app/ml/readiness/real_data.py."""
    from app.ml.readiness import real_data

    assert real_data.available(), "backend/data/external/real_campus_placement.csv must ship"
    df = real_data.load()
    assert len(df) == 10_000
    assert set(readiness.FEATURES) | {"placed"} <= set(df.columns)
    assert df["placed"].isin([0, 1]).all()
    assert real_data.REAL_DATASET_LABEL.startswith("real:")
    assert "not SRM" in real_data.REAL_DATASET_LABEL  # never implies it's our own institution


def test_ensure_model_can_bootstrap_from_the_real_dataset(tmp_path: object) -> None:
    """USE_REAL_BOOTSTRAP trains on the real dataset instead of the synthetic generator; off by
    default so the rest of the suite (and test_predict_carries_version_and_attributions above)
    keeps exercising the synthetic path."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from app.ml.readiness import real_data

    settings = SimpleNamespace(use_real_bootstrap=True, model_dir=str(tmp_path), synthetic_rows=50)
    with patch("app.ml.readiness.model.get_settings", return_value=settings):
        art = readiness.ensure_model()
    assert art["report"]["source"] == real_data.REAL_DATASET_LABEL
    assert art["report"]["n_train"] + art["report"]["n_test"] == 10_000
    assert art["report"]["fairness"] == {}  # no demographic columns in this source


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
