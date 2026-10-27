"""Readiness predictor: training (CV model selection + calibration), evaluation, inference and
per-prediction attribution."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.config import get_settings

log = logging.getLogger(__name__)

FEATURES = [
    "cgpa",
    "backlogs",
    "tenth_pct",
    "twelfth_pct",
    "internships",
    "project_count",
    "project_complexity",
    "certifications",
    "problems_solved",
    "quiz_avg",
    "resume_score",
    "interview_avg",
    "company_type_product",
]
ACADEMIC_FEATURES = ["cgpa", "backlogs", "tenth_pct", "twelfth_pct"]
LABELS = {
    "cgpa": "CGPA",
    "backlogs": "Backlogs",
    "tenth_pct": "10th %",
    "twelfth_pct": "12th %",
    "internships": "Internships",
    "project_count": "Projects",
    "project_complexity": "Project complexity",
    "certifications": "Certifications",
    "problems_solved": "Coding problems solved",
    "quiz_avg": "Quiz average",
    "resume_score": "Resume score",
    "interview_avg": "Mock interview average",
    "company_type_product": "Targets product companies",
}
SEED = 42


def _candidates() -> dict[str, Any]:
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    models: dict[str, Any] = {
        "logistic_regression": make_pipeline(
            SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1000)
        ),
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestClassifier(
                n_estimators=300, min_samples_leaf=5, random_state=SEED, n_jobs=1
            ),
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.05, random_state=SEED
        ),
    }
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05, random_state=SEED, n_jobs=1
        )
    except ImportError:
        pass
    return models


def data_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()


def _metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import accuracy_score, brier_score_loss, f1_score, roc_auc_score

    pred = (p >= 0.5).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "f1": round(float(f1_score(y, pred)), 4),
        "roc_auc": round(float(roc_auc_score(y, p)), 4),
        "brier": round(float(brier_score_loss(y, p)), 4),
    }


def _calibration_table(y: np.ndarray, p: np.ndarray, bins: int = 5) -> list[dict[str, float]]:
    edges = np.linspace(0, 1, bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if mask.sum():
            rows.append(
                {
                    "bin": f"{lo:.1f}-{hi:.1f}",
                    "n": int(mask.sum()),
                    "mean_predicted": round(float(p[mask].mean()), 3),
                    "observed_rate": round(float(y[mask].mean()), 3),
                }
            )
    return rows


def _fairness(df: pd.DataFrame, y: np.ndarray, p: np.ndarray) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    pred = (p >= 0.5).astype(int)
    for attr in ("department", "gender"):
        if attr not in df:
            continue
        rows = []
        for group in sorted(df[attr].dropna().unique()):
            m = (df[attr] == group).to_numpy()
            pos = m & (y == 1)
            rows.append(
                {
                    "group": str(group),
                    "n": int(m.sum()),
                    "selection_rate": round(float(pred[m].mean()), 3),
                    "true_positive_rate": round(float(pred[pos].mean()), 3) if pos.sum() else None,
                    "accuracy": round(float((pred[m] == y[m]).mean()), 3),
                }
            )
        out[attr] = rows
    return out


def train(df: pd.DataFrame, source: str) -> dict[str, Any]:
    """Select by 5-fold stratified CV ROC-AUC, calibrate, evaluate on a 20% hold-out."""
    from sklearn.base import clone
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

    y = df["placed"].to_numpy()
    train_df, test_df, y_train, y_test = train_test_split(
        df, y, test_size=0.2, stratify=y, random_state=SEED
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    def cv_auc(model: Any, cols: list[str]) -> dict[str, float]:
        s = cross_val_score(clone(model), train_df[cols], y_train, cv=cv, scoring="roc_auc")
        return {"mean": round(float(s.mean()), 4), "std": round(float(s.std()), 4)}

    candidates = _candidates()
    cv_results = {name: cv_auc(m, FEATURES) for name, m in candidates.items()}
    best_name = max(cv_results, key=lambda k: cv_results[k]["mean"])

    def fit_eval(cols: list[str]) -> tuple[Any, dict[str, Any], np.ndarray]:
        model = CalibratedClassifierCV(clone(candidates[best_name]), method="sigmoid", cv=5)
        model.fit(train_df[cols], y_train)
        p = model.predict_proba(test_df[cols])[:, 1]
        return model, _metrics(y_test, p), p

    model, holdout, p_test = fit_eval(FEATURES)
    _, academic_holdout, _ = fit_eval(ACADEMIC_FEATURES)

    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    dhash = data_hash(df[[*FEATURES, "placed"]])
    version = f"readiness-{best_name}-{stamp}-{dhash[:8]}"
    report = {
        "version": version,
        "source": source,
        "data_hash": dhash,
        "n_train": len(train_df),
        "n_test": len(test_df),
        "positive_rate": round(float(y.mean()), 3),
        "cv_roc_auc": cv_results,
        "selected": best_name,
        "calibration": "sigmoid (Platt), 5-fold",
        "holdout": holdout,
        "calibration_table": _calibration_table(y_test, p_test),
        "ablation": {
            "academics_only": {
                "features": ACADEMIC_FEATURES,
                "holdout": academic_holdout,
                "cv_roc_auc": cv_auc(candidates[best_name], ACADEMIC_FEATURES),
            },
            "full": {"features": FEATURES, "holdout": holdout},
        },
        "fairness": _fairness(test_df, y_test, p_test),
    }
    artifact = {
        "model": model,
        "features": FEATURES,
        "background": train_df[FEATURES].median().to_dict(),
        "report": report,
    }
    return {"artifact": artifact, "report": report}


# ---------- registry ----------


def _dir() -> Path:
    path = Path(get_settings().model_dir) / "readiness"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(artifact: dict[str, Any]) -> str:
    version = artifact["report"]["version"]
    joblib.dump(artifact, _dir() / f"{version}.joblib")
    (_dir() / f"{version}.json").write_text(json.dumps(artifact["report"], indent=2))
    (_dir() / "active.txt").write_text(version)
    _cache.clear()
    return version


_cache: dict[str, dict[str, Any]] = {}


def load_active() -> dict[str, Any] | None:
    pointer = _dir() / "active.txt"
    if not pointer.exists():
        return None
    version = pointer.read_text().strip()
    if version not in _cache:
        _cache.clear()
        _cache[version] = joblib.load(_dir() / f"{version}.joblib")
    return _cache[version]


def ensure_model() -> dict[str, Any]:
    """Load the active model; on a fresh install train one on SYNTHETIC data (labelled so)."""
    art = load_active()
    if art is None:
        from app.ml.readiness.synthetic import SYNTHETIC_LABEL, generate

        log.warning("no readiness model found; training on synthetic data")
        df = generate(get_settings().synthetic_rows)
        save(train(df, source=SYNTHETIC_LABEL)["artifact"])
        art = load_active()
        assert art is not None
    return art


# ---------- inference ----------


def predict(features: dict[str, float | None]) -> dict[str, Any]:
    art = ensure_model()
    cols = art["features"]
    row = pd.DataFrame([[features.get(c, np.nan) for c in cols]], columns=cols, dtype=float)
    prob = float(art["model"].predict_proba(row)[:, 1][0])
    return {
        "probability": round(prob, 4),
        "model_version": art["report"]["version"],
        "data_source": art["report"]["source"],
        "attributions": attribute(art, row, prob),
    }


def attribute(art: dict[str, Any], row: pd.DataFrame, prob: float) -> list[dict[str, Any]]:
    """Occlusion attribution: change in probability when one feature is reset to the training
    median. Model-agnostic and approximate; it is not SHAP (shap is not installed here)."""
    out = []
    for col in art["features"]:
        value = row.at[0, col]
        if pd.isna(value):
            continue
        probe = row.copy()
        probe.at[0, col] = art["background"][col]
        delta = prob - float(art["model"].predict_proba(probe)[:, 1][0])
        out.append(
            {
                "feature": col,
                "label": LABELS.get(col, col),
                "value": float(value),
                "baseline": float(art["background"][col]),
                "effect": round(delta, 4),
            }
        )
    out.sort(key=lambda a: abs(a["effect"]), reverse=True)
    return out
