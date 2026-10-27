"""Regenerate docs/EVALUATION.md from measured results.

    cd backend && python ../scripts/evaluate.py [--csv path/to/real_pseudonymised.csv]

Every table states its data source. Synthetic results describe the generator, not students."""

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("MODEL_DIR", str(ROOT / "backend" / "models-eval"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.ml.knowledge import bkt  # noqa: E402
from app.ml.readiness import model as readiness  # noqa: E402
from app.ml.readiness.synthetic import SYNTHETIC_LABEL, generate  # noqa: E402
from app.ml.resume.analyzer import analyze  # noqa: E402
from app.seed import SAMPLE_JDS  # noqa: E402

sys.path.insert(0, str(ROOT / "backend"))
from tests.fixtures import GAP_CASES  # noqa: E402


def table(rows: list[dict[str, object]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += [
        "| "
        + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols)
        + " |"
        for r in rows
    ]
    return "\n".join(out)


def readiness_section(csv: str | None) -> str:
    if csv:
        df, source = pd.read_csv(csv), f"CSV `{Path(csv).name}`"
    else:
        df, source = (
            generate(1500),
            f"**SYNTHETIC** generator `{SYNTHETIC_LABEL}` (n=1500)",
        )
    rep = readiness.train(df, source)["report"]
    cv = [
        {"model": k, "cv_roc_auc_mean": v["mean"], "std": v["std"]}
        for k, v in rep["cv_roc_auc"].items()
    ]
    abl = rep["ablation"]
    ablation = [
        {
            "features": "academics only (CGPA, backlogs, 10th, 12th)",
            **abl["academics_only"]["holdout"],
        },
        {"features": "full feature set", **abl["full"]["holdout"]},
    ]
    fair = []
    for attr, rows in rep["fairness"].items():
        fair += [{"attribute": attr, **r} for r in rows]
    caveat = (
        "> These numbers are measured on synthetic data. The generator assumes practice "
        "features matter more than marks, so the ablation result is built in and is **not "
        "evidence** about real students. Re-run with `--csv` on a pseudonymised pilot export.\n"
        if not csv
        else ""
    )
    return f"""## 1. Placement readiness predictor

Data: {source}. Train/test split 80/20 stratified, seed 42; positive rate {rep["positive_rate"]}.
Data hash `{rep["data_hash"][:16]}`.

{caveat}
### Model selection (5-fold stratified CV on the training split)

{table(cv, ["model", "cv_roc_auc_mean", "std"])}

Selected: **{rep["selected"]}**, calibrated with {rep["calibration"]}.

### Hold-out performance

{table([rep["holdout"]], ["accuracy", "f1", "roc_auc", "brier"])}

### Ablation: academics-only vs full features (same model family, hold-out)

{table(ablation, ["features", "accuracy", "f1", "roc_auc", "brier"])}

### Calibration (hold-out reliability table)

{table(rep["calibration_table"], ["bin", "n", "mean_predicted", "observed_rate"])}

### Fairness slices (hold-out, threshold 0.5)

{table(fair, ["attribute", "group", "n", "selection_rate", "true_positive_rate", "accuracy"])}

Explanations: occlusion attribution (feature reset to training median), not SHAP; SHAP is not
installed in this environment.
"""


def _embedders() -> list[object]:
    from app.ml.embeddings import TfidfEmbedder

    out: list[object] = [TfidfEmbedder()]
    try:
        from app.ml.embeddings import SentenceTransformerEmbedder

        out.append(SentenceTransformerEmbedder())
    except (ImportError, OSError) as exc:
        print(f"sentence-transformers unavailable, BERT row skipped: {exc}")
    return out


def skill_gap_section() -> str:
    from unittest.mock import patch

    rows = []
    for emb in _embedders():
        tp = fp = fn = 0
        with patch("app.ml.resume.analyzer.get_embedder", return_value=emb):
            for resume, jd_idx, expected in GAP_CASES:
                got = {
                    g["skill"]
                    for g in analyze(resume, SAMPLE_JDS[jd_idx])["skill_gaps"]
                }
                tp += len(got & expected)
                fp += len(got - expected)
                fn += len(expected - got)
        rows.append(
            {
                "embedder": emb.name,  # type: ignore[attr-defined]
                "precision": round(tp / (tp + fp), 2) if tp + fp else 1.0,
                "recall": round(tp / (tp + fn), 2) if tp + fn else 1.0,
                "TP": tp,
                "FP": fp,
                "FN": fn,
            }
        )
    return f"""## 2. Resume skill-gap detection

Data: {len(GAP_CASES)} **author-constructed** resume/JD pairs in `backend/tests/fixtures.py`, with
gap labels defined by construction. This is a regression check, not a human-annotated
evaluation. Both embedders' thresholds were chosen on this same set, so it overstates accuracy.

{table(rows, ["embedder", "precision", "recall", "TP", "FP", "FN"])}

`st:all-MiniLM-L6-v2` is a BERT-family sentence-transformer (enable with
`USE_SENTENCE_TRANSFORMERS=true`). Resume-to-role match precision against human judgement:
**not measured** (no human-annotated pairs yet).
"""


def kt_section() -> str:
    from sklearn.metrics import roc_auc_score

    from app.ml.knowledge import dkt

    rng = np.random.default_rng(0)
    p_true = bkt.DEFAULT
    y, scores = [], []
    for _ in range(300):
        known = rng.random() < p_true.p_init
        est = p_true.p_init
        for _ in range(12):
            correct = rng.random() < ((1 - p_true.p_slip) if known else p_true.p_guess)
            scores.append(bkt.predict_correct(est))
            y.append(int(correct))
            est = bkt.update(est, bool(correct))
            known = known or rng.random() < p_true.p_learn
    sanity = roc_auc_score(y, scores)

    try:
        res = dkt.compare()
        verdict = (
            "On this data DKT beats fitted BKT."
            if res["auc_dkt"] > res["auc_bkt_fitted"]
            else "On this data DKT does **not** beat fitted BKT."
        )
        rows = [
            {"model": "DKT (LSTM, hidden 100)", "held_out_auc": res["auc_dkt"]},
            {
                "model": "BKT, per-skill parameters fitted",
                "held_out_auc": res["auc_bkt_fitted"],
            },
            {
                "model": "BKT, default parameters",
                "held_out_auc": res["auc_bkt_default"],
            },
        ]
        comparison = f"""### DKT vs BKT

Data: **SYNTHETIC** multi-skill sequences from `dkt.simulate_sequences` ({res["skills"]} skills,
{res["learners_train"]} training and {res["learners_test"]} held-out learners, 40 answers each).
DKT hyperparameters were chosen on a separate validation split.

{table(rows, ["model", "held_out_auc"])}

{verdict} The generator is a
BKT-style process with one prerequisite link per skill, which suits BKT; DKT's advantage in the
literature comes from larger, messier real datasets. Served mastery therefore stays BKT by
default (`USE_DKT=false`).
"""
    except RuntimeError as exc:
        comparison = f"### DKT vs BKT\n\n**Not run**: {exc}\n"

    return f"""## 3. Knowledge tracing

Implementation check: BKT on **SYNTHETIC** sequences simulated from its own default parameters
(300 students x 12 attempts) gives next-attempt ROC-AUC **{sanity:.3f}**. Simulator and model share
parameters, so this only checks the code.

{comparison}
ASSISTments validation: **not run** (the dataset requires accepting its terms of use).
"""


def tracking_gain_section() -> str:
    from app.ml.knowledge import simulate
    from app.services.knowledge import target_skills

    blocks = []
    for company in ("product", "service"):
        res = simulate.run(target_skills(company), company)
        rows = [
            {"policy": r.policy, "gap_closed": r.gap_closed, "std": r.std} for r in res
        ]
        blocks.append(
            f"**{company.title()} companies** ({len(target_skills(company))} target skills): "
            f"gain vs random **{simulate.gain(res, 'random topic'):+.1%}**, vs fixed syllabus "
            f"**{simulate.gain(res, 'fixed syllabus order'):+.1%}**.\n\n"
            + table(rows, ["policy", "gap_closed", "std"])
        )
    return (
        """## 4. Skill-gap tracking gain

Data: **SYNTHETIC** learners (`app/ml/knowledge/simulate.py`, 400 per policy, 30 study sessions,
same random seed for every policy). `gap_closed` is the company-weighted share of target skills a
learner truly knows at the end. The simulator uses the same prerequisite graph and weights as the
recommender, so it shows the closed loop works as designed; it is **not** evidence of a real
learning gain, which needs a pilot with a control group.

"""
        + "\n\n".join(blocks)
        + "\n"
    )


INTERVIEW = """## 5. Mock-interview scoring

Sub-scores: content, communication, delivery (needs audio) and confidence (hedging, plus
in-browser camera signals when the student consents). Automated vs human ratings: **not
measured**. No human-rated answers exist yet. `scripts/compare_interview_ratings.py ratings.csv`
computes Pearson and Spearman r once raters score a sample (CSV columns:
`answer_id,human_overall`). Unit tests only check that clearly good answers outscore clearly poor
ones and that camera signals move confidence, never content.
"""

TARGETS = """## 6. Methodology targets vs measured

| Target (methodology poster) | Measured here | Comparable? |
|---|---|---|
| ~86% readiness accuracy | Section 1 hold-out accuracy | No: synthetic data |
| ~79% resume match precision | Section 2 fixture precision | No: 4 author-written pairs |
| r >= 0.75 interview vs human raters | Not measured | Needs human ratings |
| +25% skill-gap tracking gain | Section 4 simulated gain | No: simulator shares its assumptions |
| DKT AUC ~0.86 on ASSISTments (literature) | Section 3, synthetic only | No: different data |

The targets come from the project brief and literature and were not re-verified here. Meeting
them honestly requires the pilot (200-300 students), human-rated interviews and annotated
resume/JD pairs.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="pseudonymised CSV with readiness FEATURES + placed")
    args = ap.parse_args()
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    doc = "\n".join(
        [
            "# Evaluation\n",
            f"Generated by `scripts/evaluate.py` on {stamp}. Do not edit by hand.\n",
            readiness_section(args.csv),
            skill_gap_section(),
            kt_section(),
            tracking_gain_section(),
            INTERVIEW,
            TARGETS,
        ]
    )
    (ROOT / "docs" / "EVALUATION.md").write_text(doc, encoding="utf-8")
    print("wrote docs/EVALUATION.md")


if __name__ == "__main__":
    main()
